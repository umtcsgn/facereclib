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


import unittest
import imp
import os
import numpy
import tempfile
import facereclib
import bob
from nose.plugins.skip import SkipTest

regenerate_refs = True
#regenerate_refs = False

class ToolTest(unittest.TestCase):

  def input_dir(self, file):
    return os.path.join('testdata', 'features', file)

  def reference_dir(self, file):
    dir = os.path.join('testdata', 'tools')
    facereclib.utils.ensure_dir(dir)
    return os.path.join(dir, file)

  def config(self, file):
    return imp.load_source('config', os.path.join('config', 'tools', file))

  def ext_config(self, file):
    return imp.load_source('config', os.path.join('config', 'features', file))


  def compare(self, feature, reference):
    # execute the preprocessor
    if regenerate_refs:
      bob.io.save(feature, self.reference_dir(reference))

    self.assertTrue((numpy.abs(bob.io.load(self.reference_dir(reference)) - feature) < 1e-5).all())


  def train_set(self, feature, count = 50, a = 0, b = 1):
    # generate a random sequence of features
    numpy.random.seed(42)
    train_set = {}
    for i in range(count):
      train_set[i] = numpy.random.random(feature.shape) * (b - a) + a
    return train_set

  def train_set_by_id(self, feature, count = 50, a = 0, b = 1):
    # generate a random sequence of features
    numpy.random.seed(42)
    train_set = {}
    for i in range(count):
      per_id = {}
      for j in range(count):
        per_id[j] = numpy.random.random(feature.shape) * (b - a) + a
      train_set[i] = per_id
    return train_set

  def train_gmm_stats(self, feature_file, count = 50, a = 0, b = 1):
    # generate a random sequence of GMM-Stats features
    numpy.random.seed(42)
    train_set = {}
    f = bob.io.HDF5File(feature_file)
    for i in range(count):
      per_id = {}
      for j in range(count):
        gmm_stats = bob.machine.GMMStats(f)
        gmm_stats.sum_px = numpy.random.random(gmm_stats.sum_px.shape) * (b - a) + a
        gmm_stats.sum_pxx = numpy.random.random(gmm_stats.sum_pxx.shape) * (b - a) + a
        per_id[j] = gmm_stats
      train_set[i] = per_id
    return train_set



  def test01_gabor_jet(self):
    # read input
    feature = bob.io.load(self.input_dir('graph_with_phase.hdf5'))
    config = self.config('gabor_jet.py')
    tool = config.tool(config)

    model = tool.enroll([feature])
    self.compare(model, 'graph_model.hdf5')

    # score
    sim = tool.score(model, feature)
    self.assertAlmostEqual(sim, 1.)


  def test02_lgbphs(self):
    # read input
    feature1 = bob.io.load(self.input_dir('lgbphs_sparse.hdf5'))
    feature2 = bob.io.load(self.input_dir('lgbphs_no_phase.hdf5'))
    config = self.config('lgbphs.py')
    tool = config.tool(config)

    model = tool.enroll([feature1])
    self.compare(model, 'lgbphs_model.hdf5')

    # score
    sim = tool.score(model, feature2)
    self.assertAlmostEqual(sim, 432000.)


  def test03_pca(self):
    # read input
    feature = bob.io.load(self.input_dir('linearize.hdf5'))
    config = self.config('pca.py')
    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('pca.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=400, a=0., b=255.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('pca_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('pca_projector.hdf5'))

    # compare the resulting machines
    new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))

    self.assertEqual(tool.m_machine.shape, new_machine.shape)
    self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project feature
    projected = tool.project(feature)
    self.compare(projected, 'pca_feature.hdf5')
    self.assertTrue(len(projected.shape) == 1)

    # enrol model
    model = tool.enroll([projected])
    self.compare(model, 'pca_model.hdf5')
    sim = tool.score(model, projected)

    self.assertAlmostEqual(sim, 0.)


  def test04_pca_lda(self):
    # read input
    feature = bob.io.load(self.input_dir('linearize.hdf5'))
    config = self.config('pca+lda.py')
    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('pca+lda.hdf5')[1]
    tool.train_projector(self.train_set_by_id(feature, count=20, a=0., b=255.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('pca+lda_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('pca+lda_projector.hdf5'))

    # compare the resulting machines
    new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))

    self.assertEqual(tool.m_machine.shape, new_machine.shape)
    self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project feature
    projected = tool.project(feature)
    self.compare(projected, 'pca+lda_feature.hdf5')
    self.assertTrue(len(projected.shape) == 1)

    # enrol model
    model = tool.enroll([projected])
    self.compare(model, 'pca+lda_model.hdf5')

    # score
    sim = tool.score(model, projected)
    self.assertAlmostEqual(sim, 0.)



  def test05_bic(self):
    # read input
    feature = bob.io.load(self.input_dir('linearize.hdf5'))
    config = self.config('bic.py')
    # reduce the complexity for test purposes
    config.MAXIMUM_TRAINING_PAIR_COUNT = 100
    config.INTRA_SUBSPACE_DIMENSION = 5
    config.EXTRA_SUBSPACE_DIMENSION = 7

    tool = config.tool(config)

    # train the enroller
    t = tempfile.mkstemp('bic.hdf5')[1]
    tool.train_enroller(self.train_set_by_id(feature, count=10, a=0., b=255.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('bic_enroller.hdf5'))

    # load the projector file
    tool.load_enroller(self.reference_dir('bic_enroller.hdf5'))

    # TODO: compare BIC projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # enrol model
    model = tool.enroll([feature])
    self.compare(model, 'bic_model.hdf5')

    # score
    sim = tool.score(model, feature)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 3.753128680)


  def test06_gmm(self):
    # read input
    feature = bob.io.load(self.input_dir('dct_blocks.hdf5'))
    config = self.config('ubm_gmm.py')
    # reduce the complexity for test purposes
    config.GAUSSIANS = 2
    config.K_MEANS_TRAINING_ITERATIONS = 1
    config.GMM_TRAINING_ITERATIONS = 1

    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('gmm_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('gmm_projector.hdf5'))

    # TODO: compare GMM projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project the feature
    projected = tool.project(feature)
    if regenerate_refs:
      projected.save(bob.io.HDF5File(self.reference_dir('gmm_feature.hdf5'), 'w'))
    probe = tool.read_probe(self.reference_dir('gmm_feature.hdf5'))
    # TODO: compare the projected feature with the reference

    # enrol model with the unprojected feature
    model = tool.enroll([feature])
    if regenerate_refs:
      model.save(bob.io.HDF5File(self.reference_dir('gmm_model.hdf5'), 'w'))
    reference_model = tool.read_model(self.reference_dir('gmm_model.hdf5'))
    # TODO: compare the GMM model with the reference

    # score with projected feature
    sim = tool.score(reference_model, probe)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 931.872015904)


  def test07_isv(self):
    # read input
    feature = bob.io.load(self.input_dir('dct_blocks.hdf5'))
    config = self.config('isv.py')
    # reduce the complexity for test purposes
    config.GAUSSIANS = 2
    config.K_MEANS_TRAINING_ITERATIONS = 1
    config.GMM_TRAINING_ITERATIONS = 1
    config.JFA_TRAINING_ITERATIONS = 1

    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('isv_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('isv_projector.hdf5'))

    # TODO: compare ISV projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project the feature
    projected = tool.project(feature)
    if regenerate_refs:
      projected.save(bob.io.HDF5File(self.reference_dir('isv_feature.hdf5'), 'w'))
    # TODO: compare the projected feature with the reference
    projected_reference = tool.read_feature(self.reference_dir('isv_feature.hdf5'))

    # train the enroller
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_enroller(self.train_gmm_stats(self.reference_dir('isv_feature.hdf5'), count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('isv_enroller.hdf5'))
    tool.load_enroller(self.reference_dir('isv_enroller.hdf5'))
    # TODO: compare ISV enroler with reference
    os.remove(t)


    # enrol model with the projected feature
    model = tool.enroll([projected])
    if regenerate_refs:
      model.save(bob.io.HDF5File(self.reference_dir('isv_model.hdf5'), 'w'))
    reference_model = tool.read_model(self.reference_dir('isv_model.hdf5'))
    probe = tool.read_probe(self.reference_dir('isv_feature.hdf5'))
    # TODO: compare the GMM model with the reference

    # score with projected feature
    sim = tool.score(reference_model, probe)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 0.0004443922153)


  def test08_jfa(self):
    # read input
    feature = bob.io.load(self.input_dir('dct_blocks.hdf5'))
    config = self.config('jfa.py')
    # reduce the complexity for test purposes
    config.GAUSSIANS = 2
    config.K_MEANS_TRAINING_ITERATIONS = 1
    config.GMM_TRAINING_ITERATIONS = 1
    config.JFA_TRAINING_ITERATIONS = 1

    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('jfa_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('jfa_projector.hdf5'))

    # TODO: compare ISV projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project the feature
    projected = tool.project(feature)
    if regenerate_refs:
      projected.save(bob.io.HDF5File(self.reference_dir('jfa_feature.hdf5'), 'w'))
    # TODO: compare the projected feature with the reference
    projected_reference = tool.read_feature(self.reference_dir('jfa_feature.hdf5'))

    # train the enroller
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_enroller(self.train_gmm_stats(self.reference_dir('jfa_feature.hdf5'), count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('jfa_enroller.hdf5'))
    tool.load_enroller(self.reference_dir('jfa_enroller.hdf5'))
    # TODO: compare ISV enroler with reference
    os.remove(t)


    # enrol model with the projected feature
    model = tool.enroll([projected])
    if regenerate_refs:
      model.save(bob.io.HDF5File(self.reference_dir('jfa_model.hdf5'), 'w'))
    reference_model = tool.read_model(self.reference_dir('jfa_model.hdf5'))
    probe = tool.read_probe(self.reference_dir('jfa_feature.hdf5'))
    # TODO: compare the GMM model with the reference

    # score with projected feature
    sim = tool.score(reference_model, probe)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 0.25469123955)


  def test09_gmm_video(self):
    raise SkipTest("This test is not yet implemented")
    # read input
    feature = bob.io.load(self.input_dir('dct_blocks.hdf5'))
    config = self.config('ubm_gmm.py')
    # reduce the complexity for test purposes
    config.GAUSSIANS = 2
    config.K_MEANS_TRAINING_ITERATIONS = 1
    config.GMM_TRAINING_ITERATIONS = 1

    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('gmm_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('gmm_projector.hdf5'))

    # TODO: compare GMM projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project the feature
    projected = tool.project(feature)
    if regenerate_refs:
      projected.save(bob.io.HDF5File(self.reference_dir('gmm_feature.hdf5'), 'w'))
    probe = tool.read_probe(self.reference_dir('gmm_feature.hdf5'))
    # TODO: compare the projected feature with the reference

    # enrol model with the unprojected feature
    model = tool.enroll([feature])
    if regenerate_refs:
      model.save(bob.io.HDF5File(self.reference_dir('gmm_model.hdf5'), 'w'))
    reference_model = tool.read_model(self.reference_dir('gmm_model.hdf5'))
    # TODO: compare the GMM model with the reference

    # score with projected feature
    sim = tool.score(reference_model, probe)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 931.872015904)


  def test10_isv_video(self):
    raise SkipTest("This test is not yet implemented")
    # read input
    feature = bob.io.load(self.input_dir('dct_blocks.hdf5'))
    config = self.config('isv.py')
    # reduce the complexity for test purposes
    config.GAUSSIANS = 2
    config.K_MEANS_TRAINING_ITERATIONS = 1
    config.GMM_TRAINING_ITERATIONS = 1

    tool = config.tool(config)

    # train the projector
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_projector(self.train_set(feature, count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('isv_projector.hdf5'))

    # load the projector file
    tool.load_projector(self.reference_dir('isv_projector.hdf5'))

    # TODO: compare ISV projector with reference
    # compare the resulting machines
    #new_machine = bob.machine.LinearMachine(bob.io.HDF5File(t))
    #self.assertEqual(tool.m_machine.shape, new_machine.shape)
    #self.assertTrue(numpy.abs(tool.m_machine.weights - new_machine.weights < 1e-5).all())
    os.remove(t)

    # project the feature
    projected = tool.project(feature)
    if regenerate_refs:
      projected.save(bob.io.HDF5File(self.reference_dir('isv_feature.hdf5'), 'w'))
    # TODO: compare the projected feature with the reference
    projected_reference = tool.read_feature(self.reference_dir('isv_feature.hdf5'))

    # train the enroller
    t = tempfile.mkstemp('ubm.hdf5')[1]
    tool.train_enroller(self.train_gmm_stats(self.reference_dir('isv_feature.hdf5'), count=5, a=-5., b=5.), t)

    if regenerate_refs:
      import shutil
      shutil.copy2(t, self.reference_dir('isv_enroller.hdf5'))
    tool.load_enroller(self.reference_dir('isv_enroller.hdf5'))
    # TODO: compare ISV enroler with reference
    os.remove(t)


    # enrol model with the unprojected feature
    model = tool.enroll([projected])
    if regenerate_refs:
      model.save(bob.io.HDF5File(self.reference_dir('gmm_model.hdf5'), 'w'))
    reference_model = tool.read_model(self.reference_dir('gmm_model.hdf5'))
    probe = tool.read_probe(self.reference_dir('isv_feature.hdf5'))
    # TODO: compare the GMM model with the reference

    # score with projected feature
    sim = tool.score(reference_model, probe)
    # compare to the weired reference score ...
    self.assertAlmostEqual(sim, 0.00045667812958)

