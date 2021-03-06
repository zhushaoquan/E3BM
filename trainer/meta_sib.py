#   Copyright (c) 2020 Yaoyao Liu. All Rights Reserved.
#   Some files of this repository are modified from https://github.com/hushell/sib_meta_learn
#
#   Licensed under the Apache License, Version 2.0 (the "License").
#   You may not use this file except in compliance with the License.
#   A copy of the License is located at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   or in the "license" file accompanying this file. This file is distributed
#   on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#   express or implied. See the License for the specific language governing
#   permissions and limitations under the License.
# ==============================================================================

import argparse
import os.path as osp
import os
import tqdm
import numpy as np
import torch
import torch.nn.functional as F
from utils.misc import create_dirs, get_logger, set_random_seed
from dataloader.sib import BatchSampler, ValLoader, EpisodeSampler
from dataloader.dataset_setting_sib import dataset_setting
from networks.sib import get_featnet
from trainer.runner_sib import RunnerSIB
from models.sib import ClassifierSIB

class MetaTrainerSIB(object):
    def __init__(self, args):
        args.cache_dir = os.path.join("cache", '{}_{}shot_K{}_seed{}'.format(args.label, args.shot, args.steps_sib, args.seed_sib))
        args.log_dir = os.path.join(args.cache_dir, 'logs')
        args.out_dir = os.path.join(args.cache_dir, 'outputs')
        create_dirs([args.cache_dir, args.log_dir, args.out_dir])

        logger = get_logger(args.log_dir, args.label)
        set_random_seed(args.seed_sib)
        logger.info('Start experiment with random seed: {:d}'.format(args.seed_sib))
        logger.info(args)
        self.logger = logger

        train_transform, val_transform, self.input_w, self.input_h, train_dir, val_dir, test_dir, episode_json, nb_cls = dataset_setting(args.dataset, args.way)

        self.train_loader = BatchSampler(imgDir = train_dir, nClsEpisode=args.way, nSupport=args.shot, nQuery=args.train_query, transform=train_transform, useGPU=True, inputW=self.input_w, inputH=self.input_h, batchSize=args.batchsize_sib)
        self.test_loader = EpisodeSampler(imgDir=test_dir, nClsEpisode=args.way, nSupport=args.shot, nQuery=args.train_query, transform=val_transform, useGPU=True, inputW=self.input_w, inputH=self.input_h)
        self.val_loader = EpisodeSampler(imgDir=val_dir, nClsEpisode=args.way, nSupport=args.shot, nQuery=args.train_query, transform=val_transform, useGPU=True, inputW=self.input_w, inputH=self.input_h)
        self.args = args


    def train(self):
        device = torch.device('cuda')
        args = self.args
        netFeat, args.nFeat = get_featnet(args.backbone_sib, self.input_w, self.input_h)

        netFeat = netFeat.to(device)
        netSIB = ClassifierSIB(args.way, args.nFeat, args.steps_sib, args)
        netSIB = netSIB.to(device)

        scale_vars, wnLayerFavg_parameters, dni_parameters, hyperprior_combination_initialization_vars, hyperprior_combination_mapping_vars, hyperprior_basestep_initialization_vars, hyperprior_basestep_mapping_vars = netSIB.get_sib_parameters()

        optimizer = torch.optim.SGD([{'params': scale_vars}, {'params': wnLayerFavg_parameters, 'lr': args.lr_sib}, {'params': dni_parameters, 'lr': args.lr_sib}, {'params': hyperprior_combination_initialization_vars, 'lr': args.lr_combination}, {'params': hyperprior_combination_mapping_vars, 'lr': args.lr_combination_hyperprior}, {'params': hyperprior_basestep_initialization_vars, 'lr': args.lr_basestep}, {'params': hyperprior_basestep_mapping_vars, 'lr': args.lr_basestep_hyperprior}], args.lr, momentum=args.momentum_sib, weight_decay=args.weight_decay_sib, nesterov=True)

        criterion = torch.nn.CrossEntropyLoss()

        runner_sib = RunnerSIB(args, self.logger, netFeat, netSIB, optimizer, criterion)

        bestAcc, lastAcc, history = runner_sib.train(self.train_loader, self.val_loader)

    def eval(self):
        device = torch.device('cuda')
        args = self.args
        netFeat, args.nFeat = get_featnet(args.backbone_sib, self.input_w, self.input_h)

        netFeat = netFeat.to(device)
        netSIB = ClassifierSIB(args.way, args.nFeat, args.steps_sib, args)
        netSIB = netSIB.to(device)

        scale_vars, wnLayerFavg_parameters, dni_parameters, hyperprior_combination_initialization_vars, hyperprior_combination_mapping_vars, hyperprior_basestep_initialization_vars, hyperprior_basestep_mapping_vars = netSIB.get_sib_parameters()

        optimizer = torch.optim.SGD([{'params': scale_vars}, {'params': wnLayerFavg_parameters, 'lr': args.lr_sib}, {'params': dni_parameters, 'lr': args.lr_sib}, {'params': hyperprior_combination_initialization_vars, 'lr': args.lr_combination}, {'params': hyperprior_combination_mapping_vars, 'lr': args.lr_combination_hyperprior}, {'params': hyperprior_basestep_initialization_vars, 'lr': args.lr_basestep}, {'params': hyperprior_basestep_mapping_vars, 'lr': args.lr_basestep_hyperprior}], args.lr, momentum=args.momentum_sib, weight_decay=args.weight_decay_sib, nesterov=True)

        criterion = torch.nn.CrossEntropyLoss()

        runner_sib = RunnerSIB(args, self.logger, netFeat, netSIB, optimizer, criterion)

        runner_sib.load_ckpt(args.meta_eval_load_path)
        mean, ci95 = runner_sib.validate(self.test_loader)


