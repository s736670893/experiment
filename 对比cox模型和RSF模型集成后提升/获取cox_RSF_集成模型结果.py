import pandas as pd
import os


def handle(path, result_path):
    d = pd.read_csv(path, sep="\t", header=None)
    d.iloc[:, 0] = [float(x.split(";")[1]) for x in d.iloc[:, 0]]   # 历史原因保存的数据需要对第一列进行分割
    d = d.drop([101], axis=1)
    rsf = d.iloc[:, 0]
    cox = d.iloc[:, -1]
    max_cindex = 0
    max_pos = -1
    for i in range(d.shape[1]):
        column = d.columns[i]
        if d[column].mean() > max_cindex:
            max_cindex = d[column].mean()
            max_pos = i
    max_model = d.iloc[:, max_pos]
    result = pd.DataFrame({"rsf": rsf, "cox": cox, "cox+rsf": max_model})
    result = result[["rsf", "cox", "cox+rsf"]]
    father_path = "\\".join(result_path.split("\\")[0:-1])
    if not os.path.exists(father_path):
        os.mkdir(father_path)
    result.to_csv(result_path, sep="\t", index=None)    # 保存三种模型结果

    # 保存统计结果
    tongji_path = result_path[0:-13] + "tongji.txt"
    with open(tongji_path, "w") as fw:
        fw.write(str(rsf.mean())+"\t"+str(cox.mean())+"\t"+str(max_model.mean())+"\n")

    # 汇总信息，也就是将所有统计结果保存在一个文件中
    with open("汇总.txt", "a") as fw:
        fw.write(str(rsf.mean())+"\t"+str(cox.mean())+"\t"+str(max_model.mean())+"\n")


if __name__ == "__main__":
    diseases = ["brca", "cesc", "ov", "ucec"]
    melucular_datas = ["methylation+clinical", "miRNA+clinical", "mRNA+clinical", "RPPA+clinical"]
    root_path = "../clinical_mecoluar"
    for disease in diseases:
        for melucular in melucular_datas:
            path = os.path.join(root_path, disease, "cox+rsf", melucular, melucular+"_concordance_by_cox.txt")
            result_path = os.path.join("./三种模型结果", disease, melucular+"_all_model.txt")
            if os.path.exists(path):
                handle(path, result_path)



