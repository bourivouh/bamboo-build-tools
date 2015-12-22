# coding: utf-8
import os
import shutil
import unittest
from unittest import TestCase
from uuid import uuid4

from bamboo.git import GitHelper, GitError


class CheckTaskTestCase(TestCase):
    """ Проверяем функцию проверки возможности смержить задачу в минор
    """

    def setUp(self):
        self.git = GitHelper("TEST")
        self.path = "test_proj"

        self.init_repo()
        self.version = "1.0.0"
        self.minor = "1.1.0"

    def clean_dir(self):
        try:
            shutil.rmtree(self.path)
        except OSError:
            pass

    def tearDown(self):
        self.clean_dir()

    def init_repo(self):
        self.clean_dir()

        self.git.git(("init", self.path))
        os.chdir(self.path)

        self.make_commit("first commit")

    def make_commit(self, msg):
        fname = uuid4().hex
        with open(fname, "w") as f:
            f.write(uuid4().hex)

        self.git.git(("add", fname))
        self.git.git(("commit", "-m", msg))

    def release(self, version):
        self.git.release_candidate(version)
        self.git.release(version, self.git.get_last_tag(version))

    def create_branch(self, name):
        self.git.git(("checkout", "-b", name))

    def check_task(self, task):
        print self.git.git("log --oneline --graph".split())
        self.git.check_task(task, self.minor)

    def testTaskBeforeMinor(self):
        """ Все ок - можно мержить
        --------------- master
           \   \_______ minor
            \__________ task
        """
        branch = "task"
        self.create_branch(branch)
        self.make_commit("branch commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        self.git.get_or_create_stable(self.minor)

        self.check_task(branch)

    def testTaskInMinor(self):
        """ Все ок - можно мержить
        --------------- master
              \________ minor
                \______ task
        """
        branch = "task"
        self.release(self.version)
        self.git.get_or_create_stable(self.minor)
        self.make_commit("minor commit")

        self.create_branch(branch)
        self.make_commit("branch commit")

        self.check_task(branch)

    def testTaskEqualMinor(self):
        """ Все ок - можно мержить
        --------------  master
              |_______  minor
              \_______  task
        """
        branch = "task"
        self.release(self.version)
        self.git.get_or_create_stable(self.minor)

        self.create_branch(branch)
        self.git.checkout(branch)
        self.make_commit("branch commit")

        self.check_task(branch)

    def testTaskBeforeMerged(self):
        """ Все ок - можно мержить
        --------------- master
           \__|_____/   task
              \________ minor
        """
        branch = "task"
        self.create_branch(branch)
        self.make_commit("branch commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        self.git.get_or_create_stable(self.minor)

        self.git.checkout("master")
        self.git.merge(branch, "master", "merge task to master")

        self.check_task(branch)

    def testTaskBeforeBackMergedAfter(self):
        """ Нельзя мержить - т.к. прилетят коммиты из мастера
        --------------- master
           \__|__\_____ task
              \________ minor
        """
        branch = "task"
        self.create_branch(branch)
        self.make_commit("branch commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        self.git.get_or_create_stable(self.minor)

        self.git.checkout("master")
        self.make_commit("master commit")

        self.git.checkout(branch)
        self.git.merge("master", branch, "back merge master to task")

        with self.assertRaises(GitError):
            self.check_task(branch)

    def testTaskAfterMinor(self):
        """ Нельзя мержить - т.к. прилетят коммиты из мастера
        --------------- master
           \     \_____ task
            \__________ minor
        """
        branch = "task"
        self.release(self.version)
        self.git.get_or_create_stable(self.minor)

        self.git.checkout("master")
        self.make_commit("master commit")

        self.create_branch(branch)
        self.make_commit("task commit")

        with self.assertRaises(GitError):
            self.check_task(branch)

    def testTwoTaskOneMerged(self):
        """ Две таски - одна уже в мажоре и миноре - вторая начата вовремя.
        Можно мержить
        __.__.___._____.____ master
          |  |   \___./_____ minor
          |  \______/        task1
          \________________  task2
        """
        branch1 = "task1"
        self.create_branch(branch1)
        self.make_commit("task commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        branch2 = "task2"
        self.create_branch(branch2)
        self.make_commit("task2 commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        minor_branch = self.git.get_or_create_stable(self.minor)
        self.git.merge(branch1, minor_branch, "merge task1 to minor")

        self.git.checkout("master")
        self.git.merge(branch1, "master", "merge task1 to master")

        self.check_task(branch2)

    def testTwoTaskOneMergedOneStartedAfter(self):
        """ Две таски - одна уже в мажоре и миноре - вторая начата сразу после
        мержа первой. В мажоре больше ничего нет - можно мержить
        __.__.___.______.____ master
             |   |     /\___  task2
             |   \___./_____  minor
             \______/         task1
        """
        branch1 = "task1"
        self.create_branch(branch1)
        self.make_commit("task commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        minor_branch = self.git.get_or_create_stable(self.minor)
        self.git.merge(branch1, minor_branch, "merge task1 to minor")

        self.git.checkout("master")
        self.git.merge(branch1, "master", "merge task1 to master")

        branch2 = "task2"
        self.create_branch(branch2)
        self.make_commit("task2 commit")

        self.check_task(branch2)

    def testTwoTaskOneMergedExtraCommit(self):
        """ Две таски - одна уже в мажоре и миноре - вторая начата сразу после
        мержа первой, но в мажоре есть и другие комиты - мержить нельзя
        __.__.___.__._._.____ master
             |   |     /\___ task2
             |   \___./_____ minor
             \______/        task1
        """
        branch1 = "task1"
        self.create_branch(branch1)
        self.make_commit("task commit")

        self.git.checkout("master")
        self.make_commit("master commit")

        self.release(self.version)
        minor_branch = self.git.get_or_create_stable(self.minor)
        self.git.merge(branch1, minor_branch, "merge task1 to minor")

        self.git.checkout("master")
        self.make_commit("master commit 2")
        self.git.merge(branch1, "master", "merge task1 to master")

        branch2 = "task2"
        self.create_branch(branch2)
        self.make_commit("task2 commit")

        with self.assertRaises(GitError):
            self.check_task(branch2)


if __name__ == '__main__':
    unittest.main(verbosity=2)