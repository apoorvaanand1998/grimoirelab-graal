#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Valerio Cosentino <valcos@bitergia.com>
#

import os
import shutil
import subprocess
import tempfile
import unittest.mock

from graal.backends.core.analyzers.reverse import Reverse
from graal.backends.core.codep import (CATEGORY_CODEP,
                                       CoDep,
                                       DependencyAnalyzer,
                                       CoDepCommand)
from graal.graal import GraalError
from test_graal import TestCaseGraal
from base_analyzer import TestCaseAnalyzer


class TestCoDepBackend(TestCaseGraal):
    """CoDep backend tests"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_path = tempfile.mkdtemp(prefix='codep_')
        cls.tmp_repo_path = os.path.join(cls.tmp_path, 'repos')
        os.mkdir(cls.tmp_repo_path)

        cls.git_path = os.path.join(cls.tmp_path, 'graaltest')
        cls.worktree_path = os.path.join(cls.tmp_path, 'codep_worktrees')

        data_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(data_path, 'data')

        repo_name = 'graaltest'
        repo_path = cls.git_path

        fdout, _ = tempfile.mkstemp(dir=cls.tmp_path)

        zip_path = os.path.join(data_path, repo_name + '.zip')
        subprocess.check_call(['unzip', '-qq', zip_path, '-d', cls.tmp_repo_path])

        origin_path = os.path.join(cls.tmp_repo_path, repo_name)
        subprocess.check_call(['git', 'clone', '-q', '--bare', origin_path, repo_path],
                              stderr=fdout)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_path)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        cd = CoDep('http://example.com', self.git_path, self.worktree_path, entrypoint="module", tag='test')
        self.assertEqual(cd.uri, 'http://example.com')
        self.assertEqual(cd.gitpath, self.git_path)
        self.assertEqual(cd.worktreepath, os.path.join(self.worktree_path, os.path.split(cd.gitpath)[1]))
        self.assertEqual(cd.origin, 'http://example.com')
        self.assertEqual(cd.tag, 'test')
        self.assertEqual(cd.entrypoint, "module")

        with self.assertRaises(GraalError):
            _ = CoDep('http://example.com', self.git_path, self.worktree_path, details=True, tag='test')

    def test_fetch(self):
        """Test whether commits are properly processed"""

        cd = CoDep('http://example.com', self.git_path, self.worktree_path, entrypoint="perceval")
        commits = [commit for commit in cd.fetch()]

        self.assertEqual(len(commits), 3)
        self.assertFalse(os.path.exists(cd.worktreepath))

        commit = commits[0]
        self.assertEqual(commit['backend_name'], 'CoDep')
        self.assertEqual(commit['category'], CATEGORY_CODEP)
        result = commit['data']['analysis']
        self.assertIn('classes', result)
        self.assertTrue(type(result['classes']), dict)
        self.assertIn('nodes', result['classes'])
        self.assertTrue(type(result['classes']['nodes']), list)
        self.assertIn('links', result['classes'])
        self.assertTrue(type(result['classes']['links']), list)
        self.assertIn('packages', result)
        self.assertTrue(type(result['packages']), dict)
        self.assertTrue(type(result['packages']['nodes']), list)
        self.assertIn('links', result['packages'])
        self.assertTrue(type(result['packages']['links']), list)


class TestDependencyAnalyzer(TestCaseAnalyzer):
    """DependencyAnalyzer tests"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_path = tempfile.mkdtemp(prefix='codep_')

        data_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(data_path, 'data')

        repo_name = 'graaltest'
        cls.repo_path = os.path.join(cls.tmp_path, repo_name)

        fdout, _ = tempfile.mkstemp(dir=cls.tmp_path)

        zip_path = os.path.join(data_path, repo_name + '.zip')
        subprocess.check_call(['unzip', '-qq', zip_path, '-d', cls.tmp_path])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_path)

    def test_init(self):
        """Test initialization"""

        dep_analyzer = DependencyAnalyzer()

        self.assertIsInstance(dep_analyzer, DependencyAnalyzer)
        self.assertIsInstance(dep_analyzer.reverse, Reverse)

    def test_analyze(self):
        """Test whether the analyze method works"""

        module_path = os.path.join(self.tmp_path, 'graaltest', 'perceval')
        dep_analyzer = DependencyAnalyzer()
        result = dep_analyzer.analyze(module_path)

        self.assertIn('classes', result)
        self.assertTrue(type(result['classes']), dict)
        self.assertIn('nodes', result['classes'])
        self.assertTrue(type(result['classes']['nodes']), list)
        self.assertIn('links', result['classes'])
        self.assertTrue(type(result['classes']['links']), list)


class TestCoDepCommand(unittest.TestCase):
    """CoDepCommand tests"""

    def test_backend_class(self):
        """Test if the backend class is CoDep"""

        self.assertIs(CoDepCommand.BACKEND, CoDep)


if __name__ == "__main__":
    unittest.main()
