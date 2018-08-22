##############################################################################
# Runs the cox proportional hazards model using nfolds cross validation and
# returns the predicted risk score
#
# nfolds = number of folds in the cross validation
# dir = directory where the scripts needed will be found (lasso.R)
#
# ** requires glmnet packages
##############################################################################
library(foreach)
library(doMC)
library(randomSurvivalForest)
registerDoMC(6)

rsfcv <- function(x.train,y.train, x.test, y.test, clinical.train, clinical.test, ntree=1000) {
	source("lasso.R")
        source("cox_screen.R")
        pred.rsf <- list()

        cols.include <- cox.screen(y.train, x.train, top=sum(y.train[,2]))
        if (length(cols.include)==0)
          {
            stop("No feature passed the univariate cox screen: exit.")
          }
        x.train <- x.train[,cols.include]
        x.test <- x.test[,cols.include]
        print(paste("After univariate cox screen, features remain:", length(cols.include)))
        
        
        #Random survival forest
        if(length(cols.include)==1)
          {
            x.test <- data.frame(x.test)
            colnames(x.test) <- "x.train" # so that the formula is compatible
          }
        # data.all <- data.frame(cbind(y.train[,1],y.train[,2], x.train, clinical.train))
        # colnames(data.all)[1]="time"
        # colnames(data.all)[2]="status"
        
        
        data.test <- data.frame(cbind(x.test, clinical.test))
        data.train <- data.frame(cbind(x.train, clinical.train))

        rf.all <- rsf(Surv(time, status)~., data=data.frame(time=y.train[,1], status=y.train[,2], data.train), ntree=ntree, seed=-1)
        # rf <- rfsrc(Surv(time, status)~., data=data.frame(time=y.train[,1], status=y.train[,2], data.train), ntree=1000, seed=-1)
        feature.imp.all <- names(rf.all$importance)[which(rf.all$importance>0)] # the features with non-zero importance
        print(paste("After random forest, features remain:", length(feature.imp.all)))
        print(feature.imp.all)
        print("------------------------------------------------")
        # for(i in 1:ncol(data.frame(data.train))){
        #     print(str(data.train[i]))
        # }

        rsf.both.train <- predict(rf.all, data.frame(data.train), seed=-1)$mortality
        rsf.both.predict <- predict(rf.all, data.frame(data.test), seed=-1)$mortality
        # library(survcomp)
        # c.index.train <- concordance.index(rsf.both.train, y.train[,1], y.train[,2])$c.index
        # c.index.predict <- concordance.index(rsf.both.predict, y.test[,1], y.test[,2])$c.index
        # print(c.index.predict)
        # print(rf.all)
        # print(dim(data.train))
        # print(dim(rsf.both.train))
        # print(rsf.both.train)
        # print(dim(data.test))
        # print(dim(rsf.both.predict))
        
	return(rsf.both.predict)
}
