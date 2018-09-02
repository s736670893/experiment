import pandas as pd
import os
import numpy as np
from model.CoxAndRSFModel import cox_and_rsf_model


if __name__ == "__main__":
    filepaths = ['methylation+clinical']
    s = "methylation"
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

            concordances, predictions = cox_and_rsf_model(data, clinical, survival)

            # concordances_new=[]
            # for i in np.array(concordances):
            #     if i>0:
            #         concordances_new.append(i)
            # print("c-index-->",sum(concordances_new)/len(concordances_new))

            fw = open(filepath+"/"+filepath.lower()+"_concordance_by_cox.txt", "w")

            for concordance_col in concordances:
                fw.write(str(sum(concordance_col) / len(concordance_col)) + "; ")
                for i in concordance_col:
                    fw.write(str(i)+"\t")
                fw.write("\n")
            fw.close()

            #Save predictions to file
            predictions = np.asarray(predictions).T
            print("predictions", "\t","testSurvTime")
            # for i in range(len(predictions)):
            #     print(predictions[i][0], "\t",testSurvTime[i])
            # print (predictions)
            np.savetxt(filepath+'/predictions.csv', predictions[0], fmt='%.4g', delimiter='\t')