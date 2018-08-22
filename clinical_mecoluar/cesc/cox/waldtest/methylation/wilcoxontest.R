setwd("E:\\论文相关项目\\论文阅读\\图2\\图2a2b\\cesc\\使用SNFtool_cesc文件中的亚型重新构建模型\\cox\\waldtest\\methylation")

cesc_cli_methylation_cox_old <- read.csv("methylation+clinical_concordance_by_cox_old.txt",head = F)
cesc_cli_methylation_cox_new <- read.csv("methylation+clinical_concordance_by_cox_new.txt",head = F)
x = c(cesc_cli_methylation_cox_old['V1'])
y = c(cesc_cli_methylation_cox_new['V1'])
wilcox.test(x$V1, y$V1, paired=T) #   

'''
       Wilcoxon signed rank test with continuity correction

data:  x$V1 and y$V1
V = 2739, p-value = 0.4629
alternative hypothesis: true location shift is not equal to 0




'''