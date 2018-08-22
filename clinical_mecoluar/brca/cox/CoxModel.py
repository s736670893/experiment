import numpy as np
from sklearn.preprocessing import Imputer,LabelEncoder
import rpy2
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri


def cox_model(data, clinical, survival):
	features = data.columns
	samples = data['feature']

	data = data.values[:, 1:]
	for i in range(data.shape[1]):
		if type(data[:, i][0]) == str:
			print(111)
			le = LabelEncoder()
			le.fit(data[:, i])
			data[:, i] = le.transform(data[:, i])

	data = data.astype(np.float).T

	# clinical data
	clinical = clinical.values[:, 1:]
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
		library(randomSurvivalForest)
		library(survcomp)
		library(glmnet)
	'''
	r(r_script)
	r.source("lasso.R")
	r.source("coxcv.R")
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

		print("***************************************************")
		print("***************************************************")
		print("cox_screen + rsf: ")

		r_script_model = '''
			f1 <- function(trainData, trainSurvStatus, trainSurvTime, testData, testSurvStatus, testSurvTime, survStatus, survTime, trainIdx, testIdx, clinical_train, clinical_test){
				mySurv = Surv(survTime, survStatus)
				y.train = mySurv[trainIdx, ]
				y.test = mySurv[testIdx, ]
				predictedResponse <- coxcv(trainData, y.train, testData, y.test, clinical_train,clinical_test)
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
		r(r_script_model)
		predictedResponse = r.f1(trainData, r_trainSurvStatus, r_trainSurvTime, testData, r_testSurvStatus, r_testSurvTime,
								 r_survStatus, r_survTime, trainIdx, testIdx, clinical_train, clinical_test)
		if len(predictedResponse) > 0:
			r_script_cncordance = '''
				f2 <- function(predictedResponse, testSurvTime, testSurvStatus){
					concordance <- concordance.index(predictedResponse, testSurvTime, testSurvStatus)$c.index
					print(paste("R_concordance-->", concordance))
					print(length(predictedResponse))
					print(length(testSurvTime))
					print(length(testSurvStatus))
					return (concordance)
				}
			'''
			r(r_script_cncordance)
			print(len(predictedResponse), len(testSurvTime), len(testSurvStatus))
			concordance = r.f2(predictedResponse, testSurvTime, testSurvStatus)
			print("concordance-->", concordance)
			concordances.append(concordance)
			print(len(concordances))
			predictions.append(np.array(predictedResponse))
	return concordances, predictions
