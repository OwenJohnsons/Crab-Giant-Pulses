import psrchive 
import numpy as np 
import matplotlib.pyplot as plt
import scienceplots; plt.style.use(['science', 'no-latex'])
from lmfit import Model


def f_thick(t, t0, tau, A, offset=0.0):
    """Thick-screen model"""
    dt = np.clip(t - t0, 0.0, None)
    kernel = np.sqrt(A * np.pi * tau / (4.0 * dt**3)) * \
             np.exp(-(np.pi**2) * tau / (16.0 * dt))
    return np.nan_to_num(kernel) + offset


def f_mod_thin(t, t0, tau, A, gamma, offset=0.0):
    """Modified thin-screen model"""
    dt = np.clip(t - t0, 0.0, None)
    kernel = A * (dt**gamma) * np.exp(-dt / tau)
    return np.nan_to_num(kernel) + offset


def thick_model_func(t, t0, tau, A, offset):
    return f_thick(t, t0, tau, A, offset)

def mod_thin_model_func(t, t0, tau, A, gamma, offset):
    return f_mod_thin(t, t0, tau, A, gamma, offset)


thick_model   = Model(thick_model_func)
mod_thin_model = Model(mod_thin_model_func)


def fit_subband_thick(t, profile):
    """Fit thick-screen model to pulse window."""
    pulse_start = max(0, np.argmax(profile) - 20)
    pulse_end = min(len(profile), len(profile))
    t_pulse = t[pulse_start:pulse_end]
    y_pulse = profile[pulse_start:pulse_end] - np.min(profile[pulse_start:pulse_end])
    
    A0 = y_pulse.max()
    t0_idx = np.argmax(y_pulse)
    t0_0 = t_pulse[t0_idx]
    tau_0 = (t_pulse[-1] - t_pulse[0]) / 10.0
    max_width = (t_pulse[-1] - t_pulse[0]) * 0.5
    
    params = thick_model.make_params(t0=t0_0, tau=tau_0, A=A0, offset=0.0)
    params['tau'].min, params['tau'].max = 0.0, max_width
    params['A'].min = 0.0
    params['t0'].min, params['t0'].max = t_pulse[0], t_pulse[-1]
    params['offset'].value = np.min(y_pulse) 
    
    result = thick_model.fit(y_pulse, params, t=t_pulse)
    return result, t_pulse, y_pulse


def fit_subband_mod_thin(t, profile):
    """Fit modified thin-screen model to pulse window."""
    pulse_start = max(0, np.argmax(profile) - 20)
    pulse_end = min(len(profile), len(profile))
    t_pulse = t[pulse_start:pulse_end]
    y_pulse = profile[pulse_start:pulse_end] - np.min(profile[pulse_start:pulse_end])
    
    A0 = y_pulse.max()
    t0_idx = np.argmax(y_pulse)
    t0_0 = t_pulse[t0_idx]
    tau_0 = (t_pulse[-1] - t_pulse[0]) / 10.0
    gamma_0 = 0.1
    max_width = (t_pulse[-1] - t_pulse[0]) * 0.5
    
    params = mod_thin_model.make_params(t0=t0_0, tau=tau_0, A=A0, gamma=gamma_0, offset=0.0)
    params['tau'].min, params['tau'].max = 0.0, max_width
    params['A'].min = 0.0
    params['gamma'].min, params['gamma'].max = 0.0, 2.0
    # params['gamma'].value = 0.25
    # params['gamma'].vary = False  
    params['t0'].min, params['t0'].max = t_pulse[0], t_pulse[-1]
    params['offset'].value = np.min(y_pulse) 
    
    result = mod_thin_model.fit(y_pulse, params, t=t_pulse)
    return result, t_pulse, y_pulse


def _load_psrchive(fname, dm):
    """Load data from a PSRCHIVE file."""
    archive = psrchive.Archive_load(fname)
    archive.pscrunch()
    archive.set_dispersion_measure(dm)
    archive.dedisperse()
    archive.set_dedispersed(True)
    archive.tscrunch()
    weights = archive.get_weights().squeeze()
    waterfall = np.ma.masked_array(archive.get_data().squeeze())
    waterfall[weights == 0] = np.ma.masked
    f_channels = np.array([
        archive.get_first_Integration().get_centre_frequency(i)
        for i in range(archive.get_nchan())])
    t_res = archive.get_first_Integration().get_duration() / archive.get_nbin()

    if archive.get_bandwidth() < 0:
        waterfall = np.flipud(waterfall)
        f_channels = f_channels[::-1]

    return waterfall, f_channels, t_res


def main():
    # debug_ar = '/mnt/ucc4_data2/data/filterbanks/Crab/2026-02-02/transientx_output/Crab_61073.8131828382_cfbf00000_01_01.ar'
    debug_ar = '../DM_calc/Crab_uncorrected.ar'
    ar = debug_ar 
    waterfall, f_channels, t_res = _load_psrchive(ar, 56.711)
    
    verbose = True
    
    # supress RuntimeWarning: divide by zero encountered in true_divide
    np.seterr(divide='ignore', invalid='ignore')
    
    print(f"Waterfall shape: {waterfall.shape}")
    print(f"Frequency channels: {f_channels.shape}")
    print(f"Time resolution: {t_res}")
    
    overall_profile = np.mean(waterfall, axis=0) 
    max_idx = np.argmax(overall_profile)
    
    n_subbands = 10
    subband_size = len(f_channels) // n_subbands
    subbands = []
    for i in range(n_subbands): 
        strt_idx = i * subband_size
        end_idx = (i + 1) * subband_size if i < n_subbands - 1 else len(f_channels)
        subband_array = waterfall[strt_idx:end_idx, :] 
        subbands.append(subband_array)
        
        if verbose: 
            print(f"Frequency range for sub-band {i}: {f_channels[strt_idx]:.2f} MHz - {f_channels[end_idx-1]:.2f} MHz")
            print(f"Sub-band {i} shape: {subband_array.shape}")
    
    colors = plt.cm.cool(np.linspace(0, 1, len(f_channels)))
    fig, (ax1, ax2) = plt.subplots(
        2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 20]},
        figsize=(4, 10), constrained_layout=True, squeeze=True
    )
    
    t_full = np.arange(waterfall.shape[1]) * t_res
    ax1.plot(t_full, overall_profile, color='black')
    ax1.set_ylabel('Intensity')
    
    for i, subband in enumerate(subbands[:]):
        y_shift = i * 1.6 * overall_profile.max()  # Shift each sub-band up for visibility
        
        avg_spectrum = np.mean(subband, axis=0) 
        max_idx = np.argmax(avg_spectrum) 
        x_vals = np.arange(len(avg_spectrum)) * t_res
        # x_vals -= x_vals[max_idx]

        result_thick, t_pulse_thick, _ = fit_subband_thick(x_vals, avg_spectrum)
        result_modthin, t_pulse_modthin, _ = fit_subband_mod_thin(x_vals, avg_spectrum)
        
        if result_thick.aic < result_modthin.aic:
            best_y, t_pulse = result_thick.best_fit, t_pulse_thick
            tau_value = result_thick.params['tau'].value           # Best-fit τ
            tau_uncertainty = result_thick.params['tau'].stderr    # 1σ
            fit_report = result_thick.fit_report()
        else:
            best_y, t_pulse = result_modthin.best_fit, t_pulse_modthin
            tau_value = result_modthin.params['tau'].value           # Best-fit τ
            tau_uncertainty = result_modthin.params['tau'].stderr    # 1σ
            fit_report = result_modthin.fit_report()
        
        print('\nFrequency: {:.2f} MHz'.format(f_channels[i*subband_size + subband_size//2]))
        print(fit_report)
        # print(f"τ = {tau_value*1e3:.2f} ± {tau_uncertainty*1e3:.2f} ms, reduced χ² = {reduced_chi2:.2f} for sub-band {i} ({f_channels[i*subband_size + subband_size//2]:.2f} MHz)")
        

        ax2.scatter(x_vals, avg_spectrum + y_shift, s=5, 
                color=colors[i*subband_size + subband_size//2],
                label=f'{f_channels[i*subband_size + subband_size//2]:.2f} MHz')
    

        ax2.axhline(y_shift, color='gray', ls='--', lw=0.5)
        ax2.plot(t_pulse, (best_y - best_y.min()) + y_shift, '-', lw=1.5,
                color='k')
        half_time = 0.17
        ax2.text(half_time, y_shift + 0.8, f"{f_channels[i*subband_size + subband_size//2]:.1f} MHz, $\\tau$={tau_value*1e3:.2f} $\pm$ {tau_uncertainty*1e3:.2f} ms", fontsize=8, color='k', va='bottom')
        
   
    
    ax1.set_xlim(t_pulse.min(), t_pulse.max())
    ax2.set_xlabel('Time [s]')
    
    plt.setp(ax1.get_yticklabels(), visible=False)
    plt.setp(ax2.get_yticklabels(), visible=False)
    
    handles, labels = ax2.get_legend_handles_labels()

    # ax2.legend(handles[::-1], labels[::-1], bbox_to_anchor=(1.05, 1), loc='upper left')
    
    path_basename = ar.split('/')[-1].replace('.ar', '')
    plt.savefig(f'{path_basename}_fit.png', dpi=200)
    plt.savefig(f'{path_basename}_fit.pdf')


if __name__ == "__main__":
    main()
