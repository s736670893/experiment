# experiment
## git 使用 .gitignore：
  1. 在.gitignore文件写规则
  2. 若git status发现想要忽略的文件被跟踪，则使用git reset HEAD清除缓存区，重新上传

# git reset HEAD 和 git rm -r cached区别
  https://www.cnblogs.com/sunshine-xin/articles/3521481.html
  

# git撤销commit，但未git push的命令
在git push的时候，有时候我们会想办法撤销git commit的内容
## 1、找到之前提交的git commit的id 
git log 
找到想要撤销的id 
## 2、git reset –hard id 
完成撤销,同时将代码恢复到前一commit_id 对应的版本 
## 3、git reset id 
完成Commit命令的撤销，但是不对代码修改进行撤销，可以直接通过git commit 重新提交对本地代码的修改
