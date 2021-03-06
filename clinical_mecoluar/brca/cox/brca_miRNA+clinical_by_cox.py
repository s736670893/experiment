import numpy as np
import pandas as pd
import os
from sklearn.preprocessing import Imputer,LabelEncoder
import rpy2
import rpy2.robjects as robjects
import rpy2.robjects.numpy2ri

if __name__ == "__main__":
	# filepath = "clinical"
	# filenames = ["brca_clinical_core.txt", "brca_os_core.txt"]

	# %load_ext rmagic
	# %load_ext rpy2.ipython


	# filepaths = os.listdir()
	filepaths = ['miRNA+clinical']
	s = "miRNA"
	for filepath in filepaths:
		if os.path.isdir(filepath):
			for filename in os.listdir(filepath):
				if "os_core.txt" in filename:
					survival = pd.read_csv(filepath+"/"+filename, sep="\t")
				elif s+"_core.txt" in filename:
					data = pd.read_csv(filepath+"/"+filename, sep="\t")
				elif "_clinical_core" in filename:
					clinical = pd.read_csv(filepath+"/"+filename, sep="\t")
				elif "SNFtype" in filename:
					SNFtype = pd.read_csv(filepath+"/"+filename, sep="\t")
			data = data.merge(SNFtype, left_on="feature", right_on="patient")
			data = data.drop("patient", 1)

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
			# %R require(survival); require(randomSurvivalForest); require(survcomp); require(glmnet)
			# %R source("lasso.R")
			# %R source("coxcv.R")
			predictions=[]
			concordances=[]
			while len(concordances)<100:
				print("have run {} times".format(len(concordances)))
				#Determine Extract the training and testing sets of one bootstrap
				print(333)
				import random
				length = data.shape[1]
				trainIdx = np.array(random.sample(range(length), int(length*0.8)))
				testIdx = np.array([x for x in range(length) if not x in trainIdx])
				print("train", survStatus[trainIdx])
				print("test", survStatus[testIdx])
				# print(sorted(trainIdx))
				#Verify that the labels are the same

				#Exctract traing and testing set
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

				predictedResponse = []
				r_script_model = '''
					f1 <- function(trainData, trainSurvStatus, trainSurvTime, testData, testSurvStatus, testSurvTime, survStatus, survTime, trainIdx, testIdx, clinical_train, clinical_test){
						mySurv = Surv(survTime, survStatus)
						y.train = mySurv[trainIdx, ]
						y.test = mySurv[testIdx, ]
						predictedResponse <- coxcv(trainData, y.train, testData, y.test, clinical_train,clinical_test)
						return (predictedResponse)
					}
				'''

				rpy2.robjects.numpy2ri.activate()    # 使得numpy类型可以转换为matrix
				trainIdx = robjects.IntVector(list(map(lambda x: x + 1, trainIdx)))
				testIdx = robjects.IntVector(list(map(lambda x: x + 1, testIdx)))
				# trainData = robjects.FloatVector(trainData)
				trainSurvStatus = robjects.IntVector(trainSurvStatus)
				trainSurvTime = robjects.FloatVector(trainSurvTime)
				# testData = robjects.FloatVector(testData)
				testSurvStatus = robjects.IntVector(testSurvStatus)
				testSurvTime = robjects.FloatVector(testSurvTime)
				survStatus = robjects.IntVector(survStatus)
				survTime = robjects.FloatVector(survTime)
				# clinical_train = robjects.FloatVector(clinical_train)
				# clinical_test = robjects.FloatVector(clinical_test)
				r(r_script_model)
				predictedResponse = r.f1(trainData, trainSurvStatus, trainSurvTime, testData, testSurvStatus, testSurvTime, survStatus, survTime, trainIdx, testIdx, clinical_train, clinical_test)
				if len(predictedResponse) > 0:
					r_script_cncordance = '''
						f2 <- function(predictedResponse, testSurvTime, testSurvStatus){
							concordance <- concordance.index(predictedResponse, testSurvTime, testSurvStatus)$c.index
							return concordance
						}
					'''
					r(r_script_cncordance)
					concordance = r.f2(predictedResponse, testSurvTime, testSurvStatus)
					print (concordance)
					concordances.append(concordance)
					predictions.append(np.array(predictedResponse))


				#Push to R, model and predict
				# %Rpush trainData trainSurvStatus trainSurvTime testData testSurvStatus testSurvTime survStatus survTime trainIdx testIdx clinical_train clinical_test
				# %R mySurv = Surv(survTime, survStatus)
				# # %R for(i in trainIdx){cat(i,": ");cat(mySurv[i,],"\n")}
				# %R trainIdx = trainIdx + 1; testIdx = testIdx + 1;
				# %R y.train = mySurv[trainIdx,]
				# %R y.test = mySurv[testIdx,]

				#####################################
				## rsf model
				#####################################

				print("***************************************************")
				print("***************************************************")
				print("cox_screen + rsf: ")


				# %R -o predictedResponse predictedResponse <- coxcv(trainData, y.train, testData, y.test, clinical_train,clinical_test)
				# print(666)
				# #TODO replace this with creating the matrix of results
				# if len(predictedResponse) > 0:
				#     %R -o concordance concordance <- concordance.index(predictedResponse, testSurvTime, testSurvStatus)$c.index
				#     print (concordance)
				#     concordances.append(concordance)
				#
				#     predictions.append(np.array(predictedResponse))

			# <codecell>
			#save concordance
			concordances_new=[]
			for i in np.array(concordances):
				if i>0:
					concordances_new.append(i)
			print("c-index-->",sum(concordances_new)/len(concordances_new))

			fw = open(filepath+"/"+filepath.lower()+"_concordance_by_cox.txt",'w')
			for i in concordances:
				fw.write(str(i[0])+"\n")
			fw.close()

			#Save predictions to file
			predictions = np.asarray(predictions).T
			print("predictions", "\t","testSurvTime")
			for i in range(len(predictions)):
			    print(predictions[i][0], "\t",testSurvTime[i])
			# print (predictions)
			np.savetxt(filepath+'/predictions.csv', predictions[0], fmt='%.4g', delimiter='\t')