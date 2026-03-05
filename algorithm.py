# algorithm.py
import math
from pathlib import Path

import numpy as np
import pandas as pd


accounting = ["AR", "JAE", "JAR"]
econometrics = ["E", "JE"]
economics = ["AER", "EJ", "IER", "JET", "JIE", "JLE", "JME", "JPE_1", "JPE_2", "QJE", "RES_1", "RES_2", "RJE"]
finance = ["JF", "JFE", "JFQA", "RF", "RFS"]
information_systems = ["ISR", "JMIS", "MISQ"]
management = ["JOM", "MSOM", "MS_1", "OR", "POM"]
marketing = ["JCR", "JM", "JMR", "MS_2"]
statistics = ["AAS", "AS", "B", "JASA", "JMLR", "JRSS"]
strategy = ["AMJ", "AMR", "ASQ", "JAP", "SMJ"]

FIELD_MAP = {
    "accounting": accounting,
    "econometrics": econometrics,
    "economics": economics,
    "finance": finance,
    "information_systems": information_systems,
    "management": management,
    "marketing": marketing,
    "statistics": statistics,
    "strategy": strategy,
}
# DATA_DIR = Path("E:/website/Project/Transition_matrix")
DATA_DIR = Path(r"C:\Users\ADMIN\Desktop\Project_old\Transition_matrix")


def get_transition_matrix(P):
    P = P.copy()
    f_A = pd.DataFrame(2.0, index=P.index, columns=P.index)
    for i in range(len(P)):
        P.iloc[i, i] = 0
    return P / f_A


def get_theta_hat(tran_m, dim, C=1.2):
    d = C * tran_m.sum(axis=1).max()
    tran_m = tran_m / d

    for i in range(dim):
        tran_m.iloc[i, i] = 1 - tran_m.iloc[i].sum()

    eigenvalues, eigenvectors = np.linalg.eig(tran_m.T)
    pi_hat = eigenvectors[:, eigenvalues == eigenvalues.max()]
    pi_hat = np.array(pi_hat, dtype=float)
    pi_hat = pd.DataFrame(pi_hat, columns=["pi_hat"], index=tran_m.index)

    if pi_hat.values.sum() < 0:
        pi_hat["pi_hat"] = -pi_hat["pi_hat"]

    pi_hat["logs"] = np.log(pi_hat["pi_hat"])
    pi_hat["theta_hat"] = pi_hat["logs"] - (sum(pi_hat["logs"]) / len(pi_hat["logs"]))
    return pi_hat[["theta_hat"]], d


def get_three_elements(tran_m):
    dim = len(tran_m)
    theta_hat = get_theta_hat(tran_m, dim)[0]

    ind = tran_m.index
    f_A_fin = pd.DataFrame(1.0, index=ind, columns=ind)
    for j in ind:
        for k in ind:
            if j != k:
                f_A_fin.loc[j, k] = math.exp(float(theta_hat.loc[j, "theta_hat"])) + math.exp(
                    float(theta_hat.loc[k, "theta_hat"])
                )

    tran_m = tran_m / f_A_fin
    theta_hat_0, d = get_theta_hat(tran_m, dim)
    return theta_hat_0, f_A_fin, d


def get_tao(P, theta_hat_2, f_A_fin, d_2):
    index = theta_hat_2.index
    tao = pd.DataFrame(index=index, columns=["value"])

    for ind in index:
        others = list(index)
        others.remove(ind)
        theta_1 = float(theta_hat_2.loc[ind].values[0])

        tao_ind = 0
        for jour in others:
            f_A_0 = float(f_A_fin.loc[ind, jour])
            num = float(P.loc[ind, jour] + P.loc[jour, ind])
            theta_jour = float(theta_hat_2.loc[jour].values[0])
            tao_ind += (1 / d_2) * num * (
                1 - math.exp(theta_1) / (math.exp(theta_1) + math.exp(theta_jour))
            ) * (math.exp(theta_1) / f_A_0)

        tao.loc[ind] = tao_ind

    return tao


def get_sigma_squared(num_cluster, P, tran_m):
    index_0 = P.index
    sigma_squared_array = []

    for n in range(num_cluster):
        tran_m_0 = tran_m.loc[globals()[f"cluster_{n}"], globals()[f"cluster_{n}"]]
        P_0 = P.loc[globals()[f"cluster_{n}"], globals()[f"cluster_{n}"]]

        eff_ind = []
        for ind in P_0.index:
            if not ((P_0.loc[ind, :].sum() <= 5) | (P_0.loc[:, ind].sum() <= 5)):
                eff_ind.append(ind)

        P_0 = P_0.loc[eff_ind, eff_ind]
        tran_m_0 = tran_m_0.loc[eff_ind, eff_ind]

        theta_hat_0, f_A_fin_0, d_0 = get_three_elements(tran_m_0)
        tao_0 = get_tao(P_0, theta_hat_0, f_A_fin_0, d_0)

        index_1 = theta_hat_0.index
        sigma_squared = pd.DataFrame(index=index_1, columns=index_1)
        sigma_squared_item = pd.DataFrame(index=index_1, columns=["value"])

        for ind in index_1:
            others = list(index_1)
            others.remove(ind)

            sigma_squared_ind = 0
            theta_ind = float(theta_hat_0.loc[ind].values[0])
            tao_ind = float(tao_0.loc[ind].values[0])

            for jour in others:
                theta_jour = float(theta_hat_0.loc[jour].values[0])
                num = float(P.loc[ind, jour] + P.loc[jour, ind])
                f_A_0 = float(f_A_fin_0.loc[ind, jour])
                sigma_squared_ind += (math.exp(theta_ind) / (d_0 * tao_ind * f_A_0) ** 2) * num * math.exp(theta_jour)

            sigma_squared_item.loc[ind] = sigma_squared_ind

        for k in index_1:
            for m in index_1:
                if k != m:
                    sigma_squared.loc[k, m] = float(sigma_squared_item.loc[k].values[0]) + float(
                        sigma_squared_item.loc[m].values[0]
                    )

        full_sigma_squared = pd.DataFrame(index=index_0, columns=index_0)
        for i in eff_ind:
            for j in eff_ind:
                full_sigma_squared.loc[i, j] = sigma_squared.loc[i, j]
        sigma_squared_array.append(np.asanyarray(full_sigma_squared, dtype=np.float64))

    return sigma_squared_array


def get_conf_inv(Q_95, index, num_cluster, tran_m, P, sigma_squared_array):
    rank = pd.DataFrame()
    offset = 0

    for m in range(num_cluster):
        tran_m_0 = tran_m.loc[globals()[f"cluster_{m}"], globals()[f"cluster_{m}"]]
        P_0 = P.loc[globals()[f"cluster_{m}"], globals()[f"cluster_{m}"]]

        eff_ind = []
        for ind in P_0.index:
            if not ((P_0.loc[ind, :].sum() <= 5) | (P_0.loc[:, ind].sum() <= 5)):
                eff_ind.append(ind)

        P_0 = P_0.loc[eff_ind, eff_ind]
        tran_m_0 = tran_m_0.loc[eff_ind, eff_ind]
        theta_hat_0 = get_three_elements(tran_m_0)[0]

        conf_inv_df = pd.DataFrame(index=P_0.index, columns=P_0.index)
        for i in eff_ind:
            for j in eff_ind:
                if i != j:
                    ii = index.get_loc(i)
                    jj = index.get_loc(j)
                    sigma_km = math.sqrt(sigma_squared_array[m][ii, jj])
                    lb = -Q_95 * sigma_km - (theta_hat_0.loc[i, "theta_hat"] - theta_hat_0.loc[j, "theta_hat"])
                    ub = Q_95 * sigma_km - (theta_hat_0.loc[i, "theta_hat"] - theta_hat_0.loc[j, "theta_hat"])
                    conf_inv_df.loc[i, j] = [lb, ub]

        rank_0 = theta_hat_0.sort_values(by="theta_hat", ascending=False)
        rank_0["rank"] = [i + 1 for i in range(len(rank_0))]
        rank_0["lower_bound"] = ""
        rank_0["upper_bound"] = ""

        n = len(eff_ind)
        for i in eff_ind:
            lower_bound = 1
            upper_bound = n
            for j in eff_ind:
                if i != j:
                    if conf_inv_df.loc[j, i][1] < 0:
                        lower_bound += 1
                    if conf_inv_df.loc[j, i][0] > 0:
                        upper_bound -= 1
            rank_0.loc[i, "lower_bound"] = lower_bound
            rank_0.loc[i, "upper_bound"] = upper_bound

        for col in rank_0.columns[1:]:
            rank_0[col] = rank_0[col] + offset
        offset += n

        rank = pd.concat([rank, rank_0], axis=0)

    return rank[["rank", "lower_bound", "upper_bound"]]


def control(start_year, end_year, field=None, min_num=5, exp_threshold=0.02, Q_95=3.9):
    pub_num_path = DATA_DIR / "pub_num.parquet"
    if not pub_num_path.exists():
        raise FileNotFoundError(f"缺少数据文件: {pub_num_path}")

    pub_num = pd.read_parquet(pub_num_path)
    P = None
    for year in range(start_year, end_year + 1):
        p_path = DATA_DIR / f"transition_matrix_{year}.feather"
        if not p_path.exists():
            raise FileNotFoundError(f"缺少数据文件: {p_path}")
        yearly = pd.read_feather(p_path)
        P = yearly if P is None else (P + yearly)

    if field:
        if isinstance(field, (list, tuple, set, pd.Index, np.ndarray)):
            selected_fields = [f for f in field if f in FIELD_MAP]
            if not selected_fields:
                raise ValueError(f"field 不合法，可选: {', '.join(FIELD_MAP.keys())}")
            selected_journals = []
            for field_name in selected_fields:
                selected_journals.extend(FIELD_MAP[field_name])
            selected_journals = list(dict.fromkeys(selected_journals))
            P = P.loc[selected_journals, selected_journals]
        else:
            P = P.loc[FIELD_MAP[field], FIELD_MAP[field]]
    all_ind = P.index

    interval = end_year - start_year + 1
    citation_info = pd.DataFrame(index=all_ind, columns=["avg_citation_num", "avg_cited_num"])
    for ind in all_ind:
        citation_info.loc[ind, "avg_citation_num"] = int(P.loc[ind, :].sum() / interval)
        citation_info.loc[ind, "avg_cited_num"] = int(P.loc[:, ind].sum() / interval)

    pub_num.columns = pub_num.columns.astype(int)
    pub_num = pub_num.loc[:, start_year:end_year]
    citation_info["avg_pub_num"] = (pub_num.sum(axis=1) / interval).astype(int)

    eff_ind = []
    for ind in P.index:
        if not ((P.loc[ind, :].sum() <= 5) | (P.loc[:, ind].sum() <= 5)):
            eff_ind.append(ind)

    P = P.loc[eff_ind, eff_ind]
    ind = P.index
    tran_m = get_transition_matrix(P)
    theta_hat_1 = get_three_elements(tran_m)[0]
    theta_hat_1.sort_values(by="theta_hat", ascending=False, inplace=True)
    theta_hat_1["exp"] = np.exp(theta_hat_1["theta_hat"])
    theta_hat_1["norm"] = theta_hat_1["exp"] / sum(theta_hat_1["exp"])

    i = 0
    df = theta_hat_1.copy()
    while True:
        if len(df.loc[df["norm"] <= exp_threshold]) < min_num:
            globals()[f"cluster_{i}"] = df.index
            break
        globals()[f"cluster_{i}"] = df.loc[df["norm"] > exp_threshold].index
        df = df.loc[df["norm"] <= exp_threshold]
        df["norm"] = df["exp"] / sum(df["exp"])
        i += 1

    num_cluster = i + 1
    sigma_squared_array = get_sigma_squared(num_cluster, P, tran_m)
    conf_inv = get_conf_inv(Q_95, ind, num_cluster, tran_m, P, sigma_squared_array)
    conf_inv["confidence_interval"] = conf_inv.apply(lambda row: [int(row["lower_bound"]), int(row["upper_bound"])], axis=1)
    conf_inv.drop(columns=["lower_bound", "upper_bound"], inplace=True)
    conf_inv = pd.merge(conf_inv, citation_info, left_index=True, right_index=True)

    return conf_inv, all_ind.difference(conf_inv.index)


def build_field_df():
    all_data = []
    all_fields = []
    for field_name, field_list in FIELD_MAP.items():
        all_data.extend(field_list)
        all_fields.extend([field_name] * len(field_list))
    return pd.DataFrame({"field": all_fields}, index=all_data)


def main(start_year=2013, end_year=2015, field="economics"):
    if start_year > end_year:
        start_year, end_year = end_year, start_year

    if isinstance(field, (list, tuple, set, pd.Index, np.ndarray)):
        invalid_fields = [f for f in field if f not in FIELD_MAP]
        if invalid_fields:
            raise ValueError(f"field 不合法，可选: {', '.join(FIELD_MAP.keys())}")
    elif field and field not in FIELD_MAP:
        raise ValueError(f"field 不合法，可选: {', '.join(FIELD_MAP.keys())}")

    field_df = build_field_df()
    conf_inv, invalid = control(start_year, end_year, field)
    conf_inv = conf_inv.merge(field_df, left_index=True, right_index=True)
    conf_inv = conf_inv.reset_index().rename(columns={"index": "journal"})
    conf_inv["rank"] = conf_inv["rank"].astype(int)
    conf_inv["start_year"] = start_year
    conf_inv["end_year"] = end_year
    conf_inv = conf_inv.sort_values(by="rank").reset_index(drop=True)
    return conf_inv, list(invalid), False


if __name__ == "__main__":
    result_df, invalid_items, fallback = main()
    print(f"fallback_mode: {fallback}")
    print("invalid:", invalid_items)
    print(result_df.head(20))