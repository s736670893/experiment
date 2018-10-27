setwd("E:\\PycharmProjects\\experiment\\对比cox模型和RSF模型集成后提升")

data <- read.table("./三种模型结果\\brca\\RPPA+clinical_all_model.txt", head=T)

rsf <- data['rsf']
cox <- data['cox']
cox_rsf <- data['cox.rsf']

rsf <- cbind(molecular=rep("rsf", dim(rsf)[1]), data=rsf)
cox <- cbind(molecular=rep("cox", dim(cox)[1]), data=cox)
cox_rsf <- cbind(molecular=rep("cox+rsf", dim(cox_rsf)[1]), data=cox_rsf)

names(cox) <- c("molecular","model")
names(rsf) <- c("molecular","model")
names(cox_rsf) <- c("molecular","model")

result <- rbind(rsf, cox, cox_rsf)

library(ggolot2)

g <- ggplot(data=result, aes(x=molecular,y=V1,fill=molecular))+geom_boxplot(notch=TRUE)+scale_fill_manual(values=c("#8EE5EE","#9ACD32","#8E388E")) + geom_hline(aes(yintercept=0.5),color='red',linetype=2)+xlab(" ")+ylab("C-index")+labs(title="模型比较")