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
#     Nishchith Shetty <inishchith@gmail.com>
#

import os
import shutil
import subprocess
import tempfile
import unittest.mock

from graal.backends.core.analyzers.linguist import Linguist
from graal.backends.core.analyzers.cloc import Cloc
from graal.backends.core.colang import (CATEGORY_COLANG_LINGUIST,
                                        CATEGORY_COLANG_CLOC,
                                        CLOC,
                                        CoLang,
                                        RepositoryAnalyzer,
                                        CoLangCommand)
from graal.graal import GraalError
from test_graal import TestCaseGraal
from base_analyzer import TestCaseAnalyzer


class TestCoLangBackend(TestCaseGraal):
    """CoLang backend tests"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_path = tempfile.mkdtemp(prefix='colang_')
        cls.tmp_repo_path = os.path.join(cls.tmp_path, 'repos')
        os.mkdir(cls.tmp_repo_path)

        cls.git_path = os.path.join(cls.tmp_path, 'graaltest')
        cls.worktree_path = os.path.join(cls.tmp_path, 'colang_worktrees')

        data_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(data_path, 'data')

        repo_name = 'graaltest'
        repo_path = cls.git_path

        fdout, _ = tempfile.mkstemp(dir=cls.tmp_path)

        zip_path = os.path.join(data_path, repo_name + '.zip')
        subprocess.check_call(['unzip', '-qq', zip_path, '-d', cls.tmp_repo_path])

        cls.origin_path = os.path.join(cls.tmp_repo_path, repo_name)
        subprocess.check_call(['git', 'clone', '-q', '--bare', cls.origin_path, repo_path],
                              stderr=fdout)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_path)

    def test_initialization(self):
        """Test whether attributes are initializated"""

        cl = CoLang('http://example.com', self.git_path,
                    self.worktree_path, tag="test")
        self.assertEqual(cl.uri, 'http://example.com')
        self.assertEqual(cl.gitpath, self.git_path)
        self.assertEqual(cl.repository_path, os.path.join(
            self.worktree_path, os.path.split(cl.gitpath)[1]))
        self.assertEqual(cl.origin, 'http://example.com')
        self.assertEqual(cl.tag, 'test')

    def test_fetch_linguist(self):
        """Test whether commits are properly processed"""

        cl = CoLang('http://example.com', self.git_path, tag="test")
        commits = [commit for commit in cl.fetch()]

        self.assertEqual(len(commits), 3)
        self.assertFalse(os.path.exists(cl.worktreepath))

        commit = commits[0]
        self.assertEqual(commit['backend_name'], 'CoLang')
        self.assertEqual(commit['category'], CATEGORY_COLANG_LINGUIST)
        result = commit['data']['analysis']
        self.assertNotIn('breakdown', result)

    def test_fetch_cloc(self):
        """Test whether commits are properly processed"""

        cl = CoLang('http://example.com', self.git_path, tag="test")
        commits = [commit for commit in cl.fetch(category=CATEGORY_COLANG_CLOC)]

        self.assertEqual(len(commits), 3)
        self.assertFalse(os.path.exists(cl.worktreepath))

        commit = commits[0]
        self.assertEqual(commit['backend_name'], 'CoLang')
        self.assertEqual(commit['category'], CATEGORY_COLANG_CLOC)
        results = commit['data']['analysis']
        result = results[next(iter(results))]

        self.assertIn('blanks', result)
        self.assertTrue(type(result['blanks']), int)
        self.assertIn('comments', result)
        self.assertTrue(type(result['comments']), int)
        self.assertIn('loc', result)
        self.assertTrue(type(result['loc']), int)
        self.assertIn('total_files', result)
        self.assertTrue(type(result['total_files']), int)

    def test_fetch_unknown(self):
        """Test whether commits are properly processed"""

        cl = CoLang('http://example.com', self.git_path, tag="test")

        with self.assertRaises(GraalError):
            _ = cl.fetch(category="unknown")

    def test_metadata_category(self):
        """Test metadata_category"""

        item = {
            "Author": "Nishchith Shetty <inishchith@gmail.com>",
            "AuthorDate": "Tue Feb 26 22:06:31 2019 +0530",
            "Commit": "Nishchith Shetty <inishchith@gmail.com>",
            "CommitDate": "Tue Feb 26 22:06:31 2019 +0530",
            "analysis": [],
            "analyzer": "linguist",
            "commit": "5866a479587e8b548b0cb2d591f3a3f5dab04443",
            "message": "[copyright] Update copyright dates"
        }
        self.assertEqual(CoLang.metadata_category(item), CATEGORY_COLANG_LINGUIST)

        item = {
            "Author": "Nishchith Shetty <inishchith@gmail.com>",
            "AuthorDate": "Tue Feb 26 22:06:31 2019 +0530",
            "Commit": "Nishchith Shetty <inishchith@gmail.com>",
            "CommitDate": "Tue Feb 26 22:06:31 2019 +0530",
            "analysis": [],
            "analyzer": "cloc",
            "commit": "5866a479587e8b548b0cb2d591f3a3f5dab04443",
            "message": "[copyright] Update copyright dates"
        }
        self.assertEqual(CoLang.metadata_category(item), CATEGORY_COLANG_CLOC)

        item = {
            "Author": "Nishchith Shetty <inishchith@gmail.com>",
            "AuthorDate": "Tue Feb 26 22:06:31 2019 +0530",
            "Commit": "Nishchith Shetty <inishchith@gmail.com>",
            "CommitDate": "Tue Feb 26 22:06:31 2019 +0530",
            "analysis": [],
            "analyzer": "code_language",
            "commit": "5866a479587e8b548b0cb2d591f3a3f5dab04443",
            "message": "[copyright] Update copyright dates"
        }
        with self.assertRaises(GraalError):
            _ = CoLang.metadata_category(item, )


class TestRepositoryAnalyzer(TestCaseAnalyzer):
    """RepositoryAnalyzer tests"""

    @classmethod
    def setUpClass(cls):
        cls.tmp_path = tempfile.mkdtemp(prefix='colang_')
        cls.tmp_repo_path = os.path.join(cls.tmp_path, 'repos')
        os.mkdir(cls.tmp_repo_path)

        data_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(data_path, 'data')

        repo_name = 'graaltest'
        fdout, _ = tempfile.mkstemp(dir=cls.tmp_path)

        zip_path = os.path.join(data_path, repo_name + '.zip')
        subprocess.check_call(['unzip', '-qq', zip_path, '-d', cls.tmp_repo_path])

        cls.origin_path = os.path.join(cls.tmp_repo_path, repo_name)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_path)

    def test_init(self):
        """Test initialization"""

        repo_analyzer = RepositoryAnalyzer()
        self.assertIsInstance(repo_analyzer, RepositoryAnalyzer)
        self.assertIsInstance(repo_analyzer.analyzer, Linguist)

        repo_analyzer = RepositoryAnalyzer(kind=CLOC)
        self.assertIsInstance(repo_analyzer, RepositoryAnalyzer)
        self.assertIsInstance(repo_analyzer.analyzer, Cloc)

    def test_analyze(self):
        """Test whether the analyze method works"""

        repo_analyzer = RepositoryAnalyzer()
        result = repo_analyzer.analyze(self.origin_path)
        self.assertNotIn('breakdown', result)
        self.assertIn('Python', result)
        self.assertTrue(type(result['Python']), float)

        repo_analyzer = RepositoryAnalyzer(kind=CLOC)
        results = repo_analyzer.analyze(self.origin_path)
        result = results[next(iter(results))]

        self.assertIn('blanks', result)
        self.assertTrue(type(result['blanks']), int)
        self.assertIn('comments', result)
        self.assertTrue(type(result['comments']), int)
        self.assertIn('loc', result)
        self.assertTrue(type(result['loc']), int)
        self.assertIn('total_files', result)
        self.assertTrue(type(result['total_files']), int)


class TestCoLangCommand(unittest.TestCase):
    """CoLangCommand tests"""

    def test_backend_class(self):
        """Test if the backend class is CoLang"""

        self.assertIs(CoLangCommand.BACKEND, CoLang)


if __name__ == "__main__":
    unittest.main()
