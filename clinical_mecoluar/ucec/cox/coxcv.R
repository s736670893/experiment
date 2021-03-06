##############################################################################
# Runs the cox proportional hazards model using nfolds cross validation and
# returns the predicted 
#
# nfolds = number of folds in the cross validation
# dir = directory where the scripts needed will be found (lasso.R)
#
# ** requires glmnet packages
##############################################################################
library(foreach)
library(doMC)
registerDoMC(6)

coxcv <- function(x.train,y.train, x.test, y.test,clinical.train, clinical.test, useLASSO=TRUE) {
	source("lasso.R")
        #source("cox_screen.R")
        print(dim(y.train))
        print(dim(clinical.train))
        cox.clinical <- coxph(Surv(time, status)~., data= data.frame(time=y.train[,1], status=y.train[,2], clinical.train))
        print("666zhiqian")
        clinical.resid <- residuals(cox.clinical)
        source("correlation_screen.R")
        cols.include <- correlation.screen(clinical.resid, x.train, top=sum(y.train[,2]))
        
        if (length(cols.include)==0)
          {
            stop("No feature passed the univariate cox screen: exit.")
          }
        x.train <- x.train[,cols.include]
        x.test <- x.test[,cols.include]
      
        print(paste("After univariate cox screen, features remain:", length(cols.include)))

        if(useLASSO & length(cols.include) > 5) # further shrink by LASSO, if only few features, no need to use LASSO, note 5 is a quite arbitrary setting
          {
            # do LASSO without cross validation to get the features to include in the model
            # change x.train and x.test to only include those features
            cols.include <- c()
            iter <- 0
            while(length(cols.include)<1)
              {
                set.seed(iter+1)
                cols.include <- try(lasso(x=x.train,y=clinical.resid,above=0))
                if (class(cols.include)=="try-error")
                  {
                    print("Errors occur while calculating by LASSO, recalculating...")
                    cols.include <- c()
                  }
                iter <- iter+1
                if(iter> 1)
                  {
                    print(paste(length(cols.include)," features selected. Recalculated by LASSO:", iter))
                  }
                if(iter>100) # maximum number of iterations allowed
                  {
                    # stop("No significant features can be selected by LASSO: exit.")
                    print("No significant features can be selected by LASSO")
                  }
              }
              print(paste("After LASSO, features remain:", length(cols.include)))
              if(iter<100){
                  x.train <- x.train[,cols.include]
                  x.test <- x.test[,cols.include]
              }

          }
        #print(paste("seed =", seed, ": final features:"))
        print("------------------------------------------------")
        print(colnames(x.train))
        print("------------------------------------------------")

        # cox model for prediction
        if (length(cols.include)==1)
          {
            x.train <- data.frame(x.train)
            colnames(x.train) <- "genomic"
            x.test <- data.frame(x.test)
            colnames(x.test) <- "genomic"
          }


        all.train <- cbind(x.train, clinical.train)
        all.test <- cbind(x.test, clinical.test)
        cox.both <- coxph(Surv(time, status)~., data= data.frame(time=y.train[,1], status=y.train[,2], all.train))
        
        cox.both$coefficients[is.na(cox.both$coefficients)]=0 
        cox.both.predict <- as.matrix(all.test)%*%cox.both$coefficients
        cox.both.train <- as.matrix(all.train)%*%cox.both$coefficients

        library("survcomp")
        c.index.train <- concordance.index(cox.both.train, y.train[,1], y.train[,2])$c.index
        c.index.predict <- concordance.index(cox.both.predict, y.test[,1], y.test[,2])$c.index
        print(c.index.predict)
        
	return(cox.both.predict)
}
