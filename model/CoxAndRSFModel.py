import numpy as np
from sklearn.preprocessing import Imputer,LabelEncoder
import rpy2
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri


def cox_and_rsf_model(data, clinical, survival):
    features = data.columns
    samples = data['feature']

    data = data.values[:, 1:]
    imp = Imputer(missing_values=np.nan, strategy="median", axis=0).fit(data)
    data = imp.transform(data)
    for i in range(data.shape[1]):
        if type(data[:, i][0]) == str:
            print(111)
            le = LabelEncoder()
            le.fit(data[:, i])
            data[:, i] = le.transform(data[:, i])

    data = data.astype(np.float).T

    # clinical data
    clinical = clinical.values[:, 1:]
    for i in range(clinical.shape[0]):
        for j in range(clinical.shape[1]):
            if clinical[i, j] != clinical[i, j]:
                clinical[i, j] = "NA"

    for i in range(clinical.shape[1]):
        if type(clinical[:, i][0]) == str:
            print(111)
            le = LabelEncoder()
            le.fit(clinical[:, i])
            clinical[:, i] = le.transform(clinical[:, i])
    clinical = clinical.astype(np.float).T
    survival = survival.values[:, 1:].astype(np.float)

    survTime = survival[:, 0]
    survStatus = survival[:, 1]
    # <codecell>

    r = robjects.r
    r_script = '''
        library(survival)
        library(survcomp)
        library(glmnet)
    '''
    r(r_script)
    r.source("lasso.R")
    r.source("coxcv.R")
    r.source("rsfcv.R")
    predictions = []
    concordances = []
    while len(concordances) < 100:
        print("have run {} times".format(len(concordances)))
        # Determine Extract the training and testing sets of one bootstrap
        print(333)
        import random
        length = data.shape[1]
        trainIdx = np.array(random.sample(range(length), int(length * 0.8)))
        testIdx = np.array([x for x in range(length) if not x in trainIdx])
        print("train", survStatus[trainIdx])
        print("test", survStatus[testIdx])
        # Verify that the labels are the same

        # Exctract traing and testing set
        trainData = data[:, trainIdx].T
        trainSurvStatus = survStatus[trainIdx]
        trainSurvTime = survTime[trainIdx]
        testData = data[:, testIdx].T
        testSurvStatus = survStatus[testIdx]
        testSurvTime = survTime[testIdx]

        clinical_train = clinical[:, trainIdx].T
        clinical_test = clinical[:, testIdx].T
        # print("clinical_train-->", clinical_train)
        print("***************************************************")
        print("***************************************************")
        print("cox + rsf: ")

        r_script_cox_model = '''
            f_cox <- function(trainData, trainSurvStatus, trainSurvTime, testData, testSurvStatus, testSurvTime, survStatus, survTime, trainIdx, testIdx, clinical_train, clinical_test){
                mySurv = Surv(survTime, survStatus)
                y.train = mySurv[trainIdx, ]
                y.test = mySurv[testIdx, ]
                predictedResponse <- coxcv(trainData, y.train, testData, y.test, clinical_train ,clinical_test)
                return (predictedResponse)
            }
        '''

        r_script_rsf_model = '''
            f_rsf <- function(trainData, trainSurvStatus, trainSurvTime, testData, testSurvStatus, testSurvTime, survStatus, survTime, trainIdx, testIdx, clinical_train, clinical_test){
                mySurv = Surv(survTime, survStatus)
                y.train = mySurv[trainIdx, ]
                y.test = mySurv[testIdx, ]
                predictedResponse <- rsfcv(trainData, y.train, testData, y.test, clinical_train ,clinical_test)
                return (predictedResponse)
            }
        '''

        rpy2.robjects.numpy2ri.activate()  # 使得numpy类型可以转换为matrix
        trainIdx = robjects.IntVector(list(map(lambda x: x + 1, trainIdx)))
        testIdx = robjects.IntVector(list(map(lambda x: x + 1, testIdx)))
        # r_trainData = robjects.FloatVector(trainData)
        r_trainSurvStatus = robjects.IntVector(trainSurvStatus)
        r_trainSurvTime = robjects.FloatVector(trainSurvTime)
        # r_testData = robjects.FloatVector(testData)
        r_testSurvStatus = robjects.IntVector(testSurvStatus)
        r_testSurvTime = robjects.FloatVector(testSurvTime)
        r_survStatus = robjects.IntVector(survStatus)
        r_survTime = robjects.FloatVector(survTime)
        # r_clinical_train = robjects.FloatVector(clinical_train)
        # r_clinical_test = robjects.FloatVector(clinical_test)
        r(r_script_cox_model)
        r(r_script_rsf_model)
        predictedResponse_cox = r.f_cox(trainData, r_trainSurvStatus, r_trainSurvTime, testData, r_testSurvStatus, r_testSurvTime,
                                 r_survStatus, r_survTime, trainIdx, testIdx, clinical_train, clinical_test)
        predictedResponse_rsf = r.f_rsf(trainData, r_trainSurvStatus, r_trainSurvTime, testData, r_testSurvStatus, r_testSurvTime,
                                 r_survStatus, r_survTime, trainIdx, testIdx, clinical_train, clinical_test)

        concordance_col = []     # 101种组合
        prediction_col = []  # 101种组合
        for alpha in np.linspace(0, 1, 101):
            predictedResponse = robjects.FloatVector([alpha*predictedResponse_cox[i]+(1-alpha)*predictedResponse_rsf[i]
                                                      for i in range(len(predictedResponse_cox))])
            if len(predictedResponse) > 0:
                r_script_cncordance = '''
                    f2 <- function(predictedResponse, testSurvTime, testSurvStatus){
                        concordance <- concordance.index(predictedResponse, testSurvTime, testSurvStatus)$c.index
                        print(paste("R_concordance-->", concordance))
                        return (concordance)
                    }
                '''
                r(r_script_cncordance)
                print(len(predictedResponse), len(testSurvTime), len(testSurvStatus))
                concordance = r.f2(predictedResponse, testSurvTime, testSurvStatus)
                print("concordance-->", concordance)
                concordance_col.append(concordance[0])
                prediction_col.append(np.array(predictedResponse))
        concordances.append(concordance_col)
        print(len(concordances))
        predictions.append(prediction_col)
    return concordances, predictions
