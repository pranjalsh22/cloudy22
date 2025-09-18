import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io

st.title("Luminosity & Luminosity Density Calculator from Flux Data")
#-------------------------------------------------user define func------------------------------------------------

def snip_data(x, y, x1, x2):
    x = np.array(x)
    y = np.array(y)
    mask = (x >= x1) & (x <= x2)
    x_snipped = x[mask]
    y_snipped = y[mask]

    return x_snipped, y_snipped

#-------------------------------------------------READ FILE------------------------------------------------
uploaded_file = st.file_uploader("Upload a .txt file with tab, comma, or space delimiters", type=["txt"])

if uploaded_file is not None:
    try:
        content = uploaded_file.getvalue().decode("utf-8")
        df = pd.read_csv(io.StringIO(content), sep=None, engine='python')
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    st.header("# Uploaded Data")
    df_display = df.copy()
    for col in df.columns.tolist():
        df_display[col] = df[col].map(lambda x: f"{x:.3e}")
        
    st.dataframe(df_display)

#------------------------------------------------SELECT COLUMNS------------------------------------------------
    ohwait = st.selectbox("pick",["nuLnu","nuFnu","Fnu","Lnu"])
    columns = df.columns.tolist()
    energy_col = st.selectbox("Select the column for energy", columns)
    column2 = st.selectbox("Select the column for nuFnu", [c for c in columns if c != energy_col])

 #------------------------------------------------GIVE DISTANCE------------------------------------------------
   
    def distance():
        islog = st.toggle("input in log value?",value=True)
        if islog:
            log10_distance = st.number_input("Enter the distance in log10(cm)", value=16.49)
            distance_cm = 10 ** log10_distance
        else:
            distance_cm =st.number_input("Enter the distance in cm", value=3.086e18)
        return distance_cm
#-------------------------------------------------FIND LUMINOSIY------------------------------------------------
    A=False
    if st.button("Calculate Luminosity"):
        A=True
    if A==True:
        #- - - - - - - - - - - - - - - - - - - -CHECK VALID ENTERIES- - - - - - - - - - - - - - - - 
        energy_numeric = pd.to_numeric(df[energy_col], errors='coerce')
        invalid_energy = df[energy_numeric.isna()]
        if not invalid_energy.empty:
            st.error(f"Non-numeric values found in '{energy_col}' at rows: {invalid_energy.index.tolist()}")
            st.write("Problematic rows (energy):")
            st.dataframe(invalid_energy)
            st.stop()

        nuFnu_numeric = pd.to_numeric(df[column2], errors='coerce')
        invalid_flux = df[nuFnu_numeric.isna()]
        if not invalid_flux.empty:
            st.error(f"Non-numeric values found in '{nuFnu}' at rows: {invalid_flux.index.tolist()}")
            st.write("Problematic rows (flux):")
            st.dataframe(invalid_flux)
            st.stop()

        df[energy_col] = energy_numeric
        df[column2] = nuFnu_numeric
 #- - - - - - - - - - - - - - - - - - - -CHECK MONOTONICALLY INCREASING- - - - - - - - - - - - - - - - 

        if not df[energy_col].is_monotonic_increasing:
            unsorted_mask = df[energy_col] != df[energy_col].sort_values().values
            unsorted_rows = df[unsorted_mask]

            st.warning("Energy values were not sorted. Sorting has been applied for accurate plotting and integration.")
            st.write("### ⚠️ Rows out of order (before sorting):")
            st.dataframe(unsorted_rows)

            df = df.sort_values(by=energy_col).reset_index(drop=True)
        else:
            st.info("Energy values are already sorted.")
        #- - - - - - - - - - - - - - - - - - - -CONVERT UNITS- - - - - - - - - - - - - - - - 

        rydberg_to_erg = 2.1798723611035e-11
        h = 6.62607015e-27

        energy_raw = df[energy_col] #RYDBERG
        freq = energy_raw * rydberg_to_erg / h  # Hz
        
        #----------------------PROCESSING COLUMN 2-------------------------------
        c2 = df[column2]
        
        #nfn just means second collumn to be processed. giving meaning here :
        if ohwait=="nuFnu":
            distance_cm = distance()
            flux= np.array([a/b for a,b in zip(c2,freq)])
            lum_density = flux * 4 * np.pi * distance_cm ** 2
            lum_type = "Luminosity density (erg/s/Hz)"
        if ohwait=="Fnu":
            distance_cm = distance()
            flux=np.array(c2)
            lum_density = flux * 4 * np.pi * distance_cm ** 2
            lum_type = "Luminosity density (erg/s/Hz)"
        if ohwait=="Lnu":
            lum_density = np.array(c2)
            lum_type = "Luminosity density (erg/s/Hz)"
        if ohwait=="nuLnu":
            lum_density = np.array([a/b for a,b in zip(c2,freq)])
            lum_type = "Luminosity density (erg/s/Hz)"
        #--------------
        
        df["Luminosity_Density"] = lum_density
        df["Frequency_Hz"] = freq

        st.write(f"### Data with {lum_type}")
        df_display = df.copy()
        for col in df.columns.tolist():
            df_display[col] = df[col].map(lambda x: f"{x:.3e}")
        
        st.write(f"### Data with {lum_type} (scientific notation)")
        st.dataframe(df_display)

        fig, ax = plt.subplots()
        
        y_min = 1e-40
        y_max = 1e60
        
        plt.fill_between(np.linspace(0, 9.12e-7, 5), y_min, y_max, alpha=0.3, label='radio')
        plt.fill_between(np.linspace(9.12e-7, 9.12e-4, 5), y_min, y_max, alpha=0.3, label='microwave')
        plt.fill_between(np.linspace(9.12e-4, 0.0912, 5), y_min, y_max, alpha=0.3, label='infrared')
        plt.fill_between(np.linspace(0.0912, 0.228, 5), y_min, y_max, alpha=0.3, label='visible')
        plt.fill_between(np.linspace(0.228, 9.12, 5), y_min, y_max, alpha=0.3, label='UV')
        plt.fill_between(np.linspace(9.12, 9120, 5), y_min, y_max, alpha=0.3, label='X-ray')
        plt.fill_between(np.linspace(9120, 9.12e10, 5), y_min, y_max, alpha=0.3, label='Gamma-ray')
        

        ax.plot(energy_raw, lum_density, label=lum_type)
        ax.set_xlabel("Energy (Rydberg)")
        ax.set_ylabel("Luminosity density")
        ax.set_title(f"{lum_type} vs Energy")
        ax.set_xscale('log')
        ax.set_yscale('log')
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)

     
        total_luminosity = np.trapz(lum_density, freq)

        st.success(f"### Total Bolometric Luminosity by np: {total_luminosity:.3e} erg/s")
        
        frequencies_snipped,luminosities_snipped = snip_data(freq, lum_density,3e12,3e14)
        L_IR = np.trapz(luminosities_snipped,frequencies_snipped)

        frequencies_snipped,luminosities_snipped = snip_data(freq, lum_density,3e14,7.5e14)
        L_visible =np.trapz(luminosities_snipped,frequencies_snipped)
        
        frequencies_snipped,luminosities_snipped = snip_data(freq, lum_density,7.5e14,3e16)
        L_UV =np.trapz(luminosities_snipped,frequencies_snipped)
        
        frequencies_snipped,luminosities_snipped = snip_data(freq, lum_density,3e16,3e19)
        L_xray = np.trapz(luminosities_snipped,frequencies_snipped)
        
        df=pd.DataFrame({"Range":["IR","Visible","UV","X-ray"],"Luminosity(erg/s)":[L_IR,L_visible,L_UV,L_xray]})
                # Convert float128 to float64 in DataFrame
        df['Luminosity(erg/s)'] = df['Luminosity(erg/s)'].astype(np.float64)
        df = df.applymap(lambda x: f'{x:.2e}' if isinstance(x, (int, float)) else x)
        
        st.table(df)
