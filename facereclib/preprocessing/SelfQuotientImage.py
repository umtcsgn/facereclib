#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# @author: Manuel Guenther <Manuel.Guenther@idiap.ch> 
# @date: Thu May 24 10:41:42 CEST 2012
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bob
import numpy
from .. import utils

class SelfQuotientImage:
  """Crops the face according to the eye positions (if given), and performs histogram equalization on the resulting image"""

  def __init__(self, config):
    self.m_config = config
    self.m_color_channel = config.color_channel if hasattr(config, 'color_channel') else 'gray'
    # prepare image normalization
    real_h = config.CROP_H + 2 * config.OFFSET
    real_w = config.CROP_W + 2 * config.OFFSET
    self.m_fen = bob.ip.FaceEyesNorm(config.CROP_EYES_D, real_h, real_w, config.CROP_OH + config.OFFSET, config.CROP_OW + config.OFFSET)
    self.m_fen_image = numpy.ndarray((real_h, real_w), numpy.float64)
    self.m_fen_mask = numpy.ndarray((real_h, real_w), numpy.bool)
    self.m_sqi = bob.ip.SelfQuotientImage(sigma = config.sigma)
    self.m_sq_image = numpy.ndarray((real_h, real_w), numpy.float64) 

  def __call__(self, input_file, output_file, annotations = None):
    """Reads the input image, normalizes it according to the eye positions, and writes the resulting image"""
    image = bob.io.load(str(input_file))
    # convert to grayscale
    image = utils.gray_channel(image, self.m_color_channel)

    if annotations == None:
      sq_image = self.m_sqi(image)
      # save the image to file
      bob.io.save(sq_image, output_file)
    else:
      assert 'leye' in annotations and 'reye' in annotations
      # perform image normalization
      mask = numpy.ndarray(image.shape, numpy.bool)
      mask.fill(True)
      self.m_fen(image, mask, self.m_fen_image, self.m_fen_mask, annotations['reye'][0], annotations['reye'][1], annotations['leye'][0], annotations['leye'][1])
      self.m_sqi(self.m_fen_image, self.m_sq_image)
      self.m_sq_image[self.m_fen_mask == False] = 0.
      # save the image to file
      bob.io.save(self.m_sq_image, output_file)
      
