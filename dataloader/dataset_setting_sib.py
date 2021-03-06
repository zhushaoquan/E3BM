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

import numpy as np
import torchvision.transforms as transforms

def dataset_setting(dataset, nSupport):
    if dataset == 'MiniImageNet':
        mean = [x/255.0 for x in [120.39586422,  115.59361427, 104.54012653]]
        std = [x/255.0 for x in [70.68188272,  68.27635443,  72.54505529]]
        normalize = transforms.Normalize(mean=mean, std=std)
        trainTransform = transforms.Compose([transforms.RandomCrop(80, padding=8),
                                             transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4),
                                             transforms.RandomHorizontalFlip(),
                                             lambda x: np.asarray(x),
                                             transforms.ToTensor(),
                                             normalize
                                            ])

        valTransform = transforms.Compose([transforms.CenterCrop(80),
                                            lambda x: np.asarray(x),
                                            transforms.ToTensor(),
                                            normalize])

        inputW, inputH, nbCls = 80, 80, 64

        trainDir = './data/miniImageNet/train/'
        valDir = './data/miniImageNet/val/'
        testDir = './data/miniImageNet/test/'
        episodeJson = './data/miniImageNet/val1000Episode_5_way_1_shot.json' if nSupport == 1 \
                else './data/miniImageNet/val1000Episode_5_way_5_shot.json'

    else:
        raise ValueError('Do not support other datasets yet.')

    return trainTransform, valTransform, inputW, inputH, trainDir, valDir, testDir, episodeJson, nbCls
