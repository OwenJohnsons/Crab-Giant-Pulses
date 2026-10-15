"""
Script Purpose: To generate DM and scattering time series for the I-LOFAR Crab GP data
Required files: scatteringResults.csv (Results from modelling scattering on REALTA), DM_Phase_results.csv (Results from DM phase run on REALTA), Crab_post2011.csv (Jodrell Bank ephemeris)
Code Author: Owen Johnson 
"""

import numpy as np
import matplotlib.pyplot as plt
import scienceplots
plt.style.use(['science', 'no-latex'])
import pandas as pd
from scipy.optimize import curve_fit
from astropy.time import Time
import matplotlib.dates as mdates
from datetime import datetime
import os 


def power_law(freq, tau_150, alpha):
    """
    Power-law scattering model sampled relative to 150 MHz.
    """
    return tau_150 * (freq / 150.0) ** alpha


def fit_daily_scattering(day_group, mjd):
    """
    For one observing day:
    - group by integer frequency channel
    - take median tau in each channel
    - fit tau = tau_150 * (freq / 150)^alpha
    - return fitted tau_150 and uncertainties
    """

    freq_grouped_day = day_group.groupby('Int Frequency (MHz)')

    freqs = []
    thin_medians = []
    thick_medians = []

    for freq, freq_group in freq_grouped_day:
        freqs.append(freq)
        thin_medians.append(np.nanmedian(freq_group['Tau Thin (ms)']))
        thick_medians.append(np.nanmedian(freq_group['Tau Thick (ms)']))

    freqs = np.array(freqs, dtype=float)
    thin_medians = np.array(thin_medians, dtype=float)
    thick_medians = np.array(thick_medians, dtype=float)

    results = []

    if len(freqs) < 3:
        return results

    for model_name, tau_vals in [
        ("Thin", thin_medians),
        ("Thick", thick_medians)
    ]:
        mask = np.isfinite(freqs) & np.isfinite(tau_vals) & (tau_vals > 0)

        if np.sum(mask) < 3:
            continue

        try:
            popt, pcov = curve_fit(
                power_law,
                freqs[mask],
                tau_vals[mask],
                p0=[np.nanmedian(tau_vals[mask]), -4.0],
                maxfev=10000
            )

            tau_150, alpha = popt
            tau_150_err = np.sqrt(pcov[0, 0])
            alpha_err = np.sqrt(pcov[1, 1])

            results.append({
                "MJD": mjd,
                "Model": model_name,
                "Tau 150 MHz (ms)": tau_150,
                "Tau 150 MHz Error (ms)": tau_150_err,
                "Scattering Index": alpha,
                "Scattering Index Error": alpha_err,
                "N Pulses": len(day_group),
                "N Frequencies": np.sum(mask)
            })

        except RuntimeError:
            print(f"Fit failed for MJD {mjd}, model {model_name}")

    return results


def main():
    scattering_df = pd.read_csv("scatteringResults.csv")
    print("Dataframe shape:", scattering_df.shape)

    frequencies = scattering_df['Center Frequency (MHz)']

    scattering_df['Int Frequency (MHz)'] = frequencies.astype(int)
    freq_grouped = scattering_df.groupby('Int Frequency (MHz)')
    print("Number of subbands:", len(freq_grouped))
    colors = plt.cm.cool(np.linspace(0, 1, len(freq_grouped)))

    plt.figure(figsize=(10, 6))

    nrows = 2
    ncols = 4

    for i, freq in enumerate(sorted(freq_grouped.groups.keys())):
        if i >= nrows * ncols:
            break

        group = freq_grouped.get_group(freq)

        tau_thin = group['Tau Thin (ms)']
        tau_thick = group['Tau Thick (ms)']

        ax = plt.subplot(nrows, ncols, i + 1)

        ax.hist(tau_thin, bins=20, alpha=0.5, label='Thin', color='blue')
        ax.hist(tau_thick, bins=20, alpha=0.5, label='Thick', color='red')

        ax.set_title(f"{freq} MHz")
        ax.set_ylabel("Frequency")
        ax.legend()

    plt.tight_layout()
    plt.savefig("scatteringHistogram.png", dpi=200)
    plt.close()

    scattering_df['Int MJD'] = scattering_df['MJD'].astype(int)
    mjd_grouped = scattering_df.groupby('Int MJD')
    print("Number of days:", len(mjd_grouped))

    daily_results = []

    for mjd, day_group in mjd_grouped:
        if len(day_group) <= 15:
            continue

        day_results = fit_daily_scattering(day_group, mjd)
        daily_results.extend(day_results)

    daily_scattering_df = pd.DataFrame(daily_results)

    daily_scattering_df.to_csv("dailyScattering150MHz.csv", index=False)

    print("Saved daily scattering results to dailyScattering150MHz.csv")
    print(daily_scattering_df.head())
    
    daily_scattering_df["Date"] = Time(
        daily_scattering_df["MJD"].values,
        format="mjd"
    ).to_datetime()

    thin_df = daily_scattering_df[daily_scattering_df["Model"] == "Thin"]
    thick_df = daily_scattering_df[daily_scattering_df["Model"] == "Thick"]

    plt.figure(figsize=(9, 3))

    plt.errorbar(
        thin_df["Date"],
        thin_df["Tau 150 MHz (ms)"],
        yerr=thin_df["Tau 150 MHz Error (ms)"],
        fmt="o",
        capsize=3,
        label="Thin",
        color=colors[2],
        # ecolor='black',
        markersize=2
        # markerfacecolor='none'
    )

    plt.errorbar(
        thick_df["Date"],
        thick_df["Tau 150 MHz (ms)"],
        yerr=thick_df["Tau 150 MHz Error (ms)"],
        fmt="s",
        capsize=3,
        label="Thick",
        color=colors[-2],
        # ecolor='black',
        markersize=2
        # markerfacecolor='none'
    )
    

    plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m"))
    plt.gca().xaxis.set_major_locator(plt.matplotlib.dates.MonthLocator(interval=6))
    plt.ylabel(r"Scattering timescale, $\tau_{150}$ [ms]")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(axis='y', alpha=0.3)

    plt.savefig("dailyScattering150MHz_vs_month.png", dpi=200)
    plt.savefig("dailyScattering150MHz_vs_month.pdf", dpi=200)
    plt.close()
    
    # plot thin and thick scattering vs DM 
    # --- Observational Data --- 
    crab_df = pd.read_csv('../DM_calc/DM_Phase_results.csv')
    crab_df = crab_df[crab_df['MJD'] > 0].copy()


    crab_mjds = crab_df['MJD'].values
    crab_df['MJD_day'] = crab_mjds.astype(int)

    # Brightest per day
    daily_max = crab_df.loc[crab_df.groupby('MJD_day')['SNR'].idxmax()][['MJD_day', 'DM', 'DM_std', 'SNR', 'MJD']]
    daily_max['Date'] = Time(daily_max['MJD'].values, format="mjd").datetime
        
    # match scattering data to DM data by MJD_day
    merged_df = daily_scattering_df.merge(
        daily_max,
        left_on='MJD',
        right_on='MJD_day',
        how='inner') 
    plt.figure(figsize=(9, 3))
    plt.errorbar(
        merged_df["DM"],
        merged_df["Tau 150 MHz (ms)"],
        yerr=merged_df["Tau 150 MHz Error (ms)"],
        fmt="o",
        capsize=3,
        label="Thin",
        color=colors[2],
        # ecolor='black',
        markersize=2
        # markerfacecolor='none'
    )
    plt.xlabel("DM [pc cm$^{-3}$]")
    plt.ylabel(r"Scattering timescale, $\tau_{150}$ [ms]")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("dailyScattering150MHz_vs_DM.png", dpi=200)
    
     # --- Jodrell Bank ephemeris ---
    jodrell_df = pd.read_csv("../data/Crab_post2011.csv")
    jodrell_dates = pd.to_datetime(jodrell_df["Date"], dayfirst=True)
    jodrell_dm = jodrell_df["DM_pc_cm-3"].values

    # Keep brightest-burst DM after 2020
    daily_max_plot = daily_max[daily_max["Date"] >= datetime(2020, 1, 1)].copy()
    
    # Cross correlation between DM and scattering timescale
    # correlation = np.correlate(daily_max_plot["DM"], daily_scattering_df["Tau 150 MHz (ms)"])
    # print("Cross-correlation between DM and scattering timescale:", correlation)
    # correlation_coeff = np.corrcoef(daily_max_plot["DM"], daily_scattering_df["Tau 150 MHz (ms)"][:len(daily_max_plot)])
    # print("Correlation coefficient between DM and scattering timescale:", correlation_coeff[0, 1])
    
#     print('Keys in daily_max_plot:', daily_max_plot.columns)
#     merged = daily_max_plot[['MJD_day', 'DM']].merge(
#     daily_scattering_df[['MJD', 'Tau 150 MHz (ms)']],
#     on='MJD_day',
#     how='inner'
# )

#     r = np.corrcoef(merged['DM'], merged['Tau 150 MHz (ms)'])[0, 1]
#     print(r)

    fig, (ax1, ax2) = plt.subplots(
        2, 1,
        figsize=(9, 5),
        sharex=True,
        gridspec_kw={"height_ratios": [1, 1]}
    )

    # Top: daily scattering
    ax2.errorbar(
        thin_df["Date"],
        thin_df["Tau 150 MHz (ms)"],
        yerr=thin_df["Tau 150 MHz Error (ms)"],
        fmt="o",
        capsize=3,
        label="Thin",
        color=colors[2],
        ecolor="grey",
        markersize=2
    )

    ax2.errorbar(
        thick_df["Date"],
        thick_df["Tau 150 MHz (ms)"],
        yerr=thick_df["Tau 150 MHz Error (ms)"],
        fmt="s",
        capsize=3,
        label="Thick",
        color=colors[-2],
        ecolor="grey",
        markersize=2
    )

    ax2.set_ylabel(r"$\tau_{150}$ [ms]")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    # Bottom: brightest-burst DM + Jodrell ephemeris
    ax1.step(
        jodrell_dates,
        jodrell_dm,
        where="post",
        label="Jodrell Bank Ephemeris",
        color="k"
    )

    ax1.errorbar(
        daily_max_plot["Date"],
        daily_max_plot["DM"],
        yerr=daily_max_plot["DM_std"],
        fmt="o",
        color=colors[-2],
        ecolor="grey",
        capsize=2,
        label="Brightest burst per day",
        markersize=2.5
    )

    ax1.set_ylabel(r"DM [pc cm$^{-3}$]")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

    ax2.set_xlim(datetime(2020, 1, 1), datetime(2026, 4, 1))
    plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    plt.savefig("scattering_and_DM_shared_x.png", dpi=200)
    plt.savefig("scattering_and_DM_shared_x.pdf", dpi=200)
    plt.close()
    
    
    x = daily_max_plot["DM"].astype(float).reset_index(drop=True).to_numpy()
    y = daily_scattering_df["Tau 150 MHz (ms)"].astype(float).reset_index(drop=True).to_numpy()

    n = min(len(x), len(y))
    x = x[:n]
    y = y[:n]

    mask = np.isfinite(x) & np.isfinite(y)
    x = x[mask] - np.mean(x[mask])
    y = y[mask] - np.mean(y[mask])

    ccf = np.correlate(x, y, mode="full")
    lags = np.arange(-len(x) + 1, len(x))
    ccf_norm = ccf / (np.std(x) * np.std(y) * len(x))

    best_idx = np.argmax(ccf_norm)
    best_lag = lags[best_idx]
    best_r = ccf_norm[best_idx]

    os.makedirs("output", exist_ok=True)
    pd.DataFrame({"lag_days": lags, "cross_correlation": ccf_norm}).to_csv(
        "output/cross_correlation_vs_lag.csv", index=False
    )

    plt.figure(figsize=(6, 5))
    plt.plot(lags, ccf_norm, color="black")
    plt.axvline(best_lag, color="red", linestyle="--", linewidth=1)
    plt.scatter([best_lag], [best_r], color="red", s=30)
    plt.xlabel("Lag days")
    plt.xlim(-150, 150)
    plt.ylabel("Cross-correlation")
    # plt.title("DM vs Tau cross-correlation vs lag")
    plt.tight_layout()
    plt.savefig("output/cross_correlation.pdf", dpi=200)
    # plt.show()

    print("Best lag:", best_lag)
    print("Peak correlation:", best_r)
  

 

if __name__ == "__main__":
    main()