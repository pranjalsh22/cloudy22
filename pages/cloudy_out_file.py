#version7

import re
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
#from io import StringIO

#-------------------- USER DEFINED FUNCTIONS---------------------------------------------

def extract_cloudy_data(file_content):
    wavelengths = []
    luminosities = []
    labels = []
    rel_luminosities = []

    cleaned = re.sub(r'\b\w+\.\.+\s*', ' ', file_content)
    normalized = re.sub(r'\s+', ' ', cleaned)

    # Updated regex: accept * in second luminosity field
    pattern = re.compile(r"([\w\s]+?)\s+([\d.]+)(A|m)\s+([\d.eE+-]+)\s+([\d.eE+-]+|\*+)")

    matches = pattern.findall(normalized)

    for match in matches:
        label, value, unit, lum1, lum2 = match
        try:
            # Skip if first luminosity value is corrupted (contains *)
            if '*' in lum1:
                continue

            wavelength = float(value)
            luminosity = float(lum1)
            #rel_luminosity = float(lum2)
            if unit == "m":
                wavelength *= 1e4  # convert microns to angstroms

            labels.append(label.strip())
            wavelengths.append(wavelength)
            luminosities.append(luminosity)
            #rel_luminosities.append(rel_luminosity)

        except ValueError:
            continue

    return wavelengths, luminosities, labels #, rel_luminosities

def find_warnings(file_content):
    warnings=[]
    for line in file_content.splitlines():
        if any(keyword in line.lower() for keyword in ["warning", "caution"]):
            warnings.append(line.strip())
    return warnings

def final_iteration_content(content):
    #st.text_area(content)
    final_iter_match = re.search(r'Cloudy ends:.*?(\d+)\s+iterations?', content)


    if final_iter_match:

        st.info(f"Number of iterations: {final_iter_match.group(1)}")

    else:

        st.error("Could not determine number of iterations.")

        return None

    
    st.info(f"Number of iterations:{final_iter_match[1]}")
    if final_iter_match:
        final_iteration = int(final_iter_match.group(1))
        iteration_pattern = fr'iteration\s+{final_iteration}\b'
        iter_match = list(re.finditer(iteration_pattern, content, re.IGNORECASE))
        if iter_match:
            
            match = re.search(fr'iteration\s+{final_iteration}', content, re.IGNORECASE)
            if match:
                
                # Slice content starting after 'iteration 6'
                content_after = content[match.end():]
                
                return content_after
        else:
            st.write(f"'content of iteration {final_iteration}' not found in file.")
    else:
        st.write("Could not find final iteration in 'Cloudy ends' line.")

def extract_emergent_lines(content):
    if content==None:
        st.warning("No data passed into extract_emergent_lines() ")
    else:
        pattern = r"Emergent line intensities"
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return content[match.end():]  # Return everything after the header
        else:
            st.warning("Could not find 'Emergent line intensities' block.")
            return ""
def is_main_line(label, wavelength, main_lines, main_wavelengths, tol=0.5):
    label = label.strip().lower()

    label_match = any(x in label for x in main_lines)

    wavelength_match = any(
        abs(wavelength - w) <= tol
        for w in main_wavelengths
    )

    return label_match or wavelength_match
#-----------------------------APP START--------------------------------------------
st.title("Cloudy Output File Processor")
st.write("Upload a Cloudy output file to extract and visualize line luminosities, and explore other results.")

uploaded_files = st.file_uploader(
    "Upload Cloudy Output Files",
    type=["txt", "out"],
    accept_multiple_files=True)

st.subheader("Global Analysis Settings")

# ---------------- Highlight labels ----------------

main_lines_input = st.text_input("Emission line labels to highlight (comma separated)",value="o 3, o3bn")

main_lines = [
    line.strip().lower()
    for line in main_lines_input.split(",")
    if line.strip()
]

# ---------------- Main wavelengths ----------------

main_wavelength_input = st.text_input(
    "Main wavelengths (Å, comma separated)",
    value="4363,5007"
)

main_wavelengths = [
    float(x)
    for x in main_wavelength_input.split(",")
    if x.strip()
]

if uploaded_files:

    for uploaded_file in uploaded_files:

        with st.expander(f"📄 {uploaded_file.name}", expanded=False):

            warnings = find_warnings(file_content)
            content1 = final_iteration_content(file_content)
            content = extract_emergent_lines(content1)
            wavelengths, luminosities, labels = extract_cloudy_data(content)

            line_data = pd.DataFrame({
                "Label": labels,
                "Wavelength(Å)": wavelengths,
                "luminosity(erg/s)": luminosities,
            })

            #-----
            file_content = uploaded_file.getvalue().decode(
                "utf-8",
                errors="replace"
            )
            
            
            warnings = find_warnings(file_content)
            
            content1 = final_iteration_content(file_content)
            
            content = extract_emergent_lines(content1)
            
            wavelengths, luminosities, labels = extract_cloudy_data(content)
            
            line_data = pd.DataFrame({
                "Label": labels,
                "Wavelength(Å)": wavelengths,
                "luminosity(erg/s)": luminosities,
            })
            #------

        
            # Display Input Parameters at the Start
            st.subheader("Input Parameters")
            st.write("### Total Emission Lines Extracted:", len(wavelengths))
            if st.checkbox("See warnings",key=f"warnings_{uploaded_file.name}"):
                st.write("### Warnings:")
                st.write("\n \n".join(warnings) if warnings else "No additional results found.")

        #--------------------GRAPH 1: ONLY MAIN LINES------------------------------
            st.subheader("Main Emission Lines Only")
            #main_wavelengths = [4363,4363.21,4958.91,5006.84,4931.23,5007]  # example wavelengths in Å
            st.write(f"looking for wavelengths(Å) :{main_wavelengths}")
            main_data = line_data[
                line_data.apply(
                    lambda row: is_main_line(
                        row["Label"],
                        row["Wavelength(Å)"],
                        main_lines,
                        main_wavelengths
                    ),
                    axis=1
                )
            ]
            st.dataframe(main_data,use_container_width=True)
            
            if not main_data.empty:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.bar(
                    main_data["Wavelength(Å)"],
                    main_data["luminosity(erg/s)"],
                    width=5.0,
                    color="green",
                    edgecolor="black",
                    linewidth=0.3,
                    alpha=0.8
                )

                # Annotate each line with its label
                for _, row in main_data.iterrows():
                    ax.text(row["Wavelength(Å)"], row["luminosity(erg/s)"] + 0.1, row["Label"],
                            fontsize=10, color="darkgreen")

                ax.set_title("Main Emission Lines", fontsize=16)
                ax.set_xlabel("Wavelength (Å)", fontsize=14)
                ax.set_ylabel("Log(luminosity) [erg/s]", fontsize=14)
                #ax.set_ylim(bottom=0)
                ax.set_ylim(
                    min(main_data["luminosity(erg/s)"]) - 1,
                    max(main_data["luminosity(erg/s)"]) + 1
                )
                # User input for custom X-axis range
                st.subheader("Set X-Axis Range for Main Emission Line Plot")
                col1, col2 = st.columns(2)
                default_min_x = int(main_data["Wavelength(Å)"].min()) - 200
                default_max_x = int(main_data["Wavelength(Å)"].max()) + 200

                with col1:

                    key = f"minx_{uploaded_file.name}"

                    if key not in st.session_state:
                        st.session_state[key] = default_min_x

                    min_x = st.number_input("Minimum Wavelength (Å)",key=key)
                    

                with col2:
                    max_x = st.number_input(
                        "Maximum Wavelength (Å)",
                        value=default_max_x,
                        key=f"maxx_{uploaded_file.name}"
                    )
                st.write(main_data["Wavelength(Å)"].min(), main_data["Wavelength(Å)"].max())
                ax.set_xlim(min_x, max_x)
                ax.grid(axis="y", linestyle="--", alpha=0.6)
                
                st.pyplot(fig)
            else:
                st.write("No main emission lines found in the data.")


        #--------------------GRAPH 2:FILTERED GRAPH------------------------------
            # Display the emission lines in a scrollable box
            st.subheader("Emission Line Strengths")
            
            st.dataframe(line_data, height=300, use_container_width=True)

            st.subheader("Filter Emission Lines by Wavelength and Log(luminosity)")

            # Input for wavelength range
            min_wavelength = st.number_input(
                "Minimum Wavelength (Å)",
                min_value=int(min(wavelengths)),
                max_value=int(max(wavelengths)),
                value=int(min(wavelengths)),key=f"minwavw_{uploaded_file.name}"
            )

            max_wavelength = st.number_input(
                "Maximum Wavelength (Å)",
                min_value=int(min(wavelengths)),
                max_value=int(max(wavelengths)),
                value=int(max(wavelengths)),key=f"maxwavw_{uploaded_file.name}"
            )

            # Input for log luminosity range
            min_luminosity = st.number_input(
                "Minimum Log(luminosity)",
                min_value=int(min(luminosities)),
                max_value=int(max(luminosities)),
                value=int(min(luminosities)),key=f"minlum_{uploaded_file.name}"
            )

            max_luminosity = st.number_input(
                "Maximum Log(luminosity)",
                min_value=int(min(luminosities)),
                max_value=int(max(luminosities)),
                value=int(max(luminosities)),key=f"maxlum_{uploaded_file.name}"
            )

            # Filter the line data based on the selected ranges
            filtered_data = line_data[
                (line_data["Wavelength(Å)"] >= min_wavelength) & 
                (line_data["Wavelength(Å)"] <= max_wavelength) & 
                (line_data["luminosity(erg/s)"] >= min_luminosity) & 
                (line_data["luminosity(erg/s)"] <= max_luminosity)
            ]

            # Display filtered data
            st.write(f"### Filtered Emission Lines (Wavelength: {min_wavelength} - {max_wavelength} Å, Log(luminosity): {min_luminosity} - {max_luminosity})")
            if not filtered_data.empty:
                st.dataframe(filtered_data, height=300, use_container_width = True)

                # Plotting Section: Plot the filtered data
                st.write("### Plot the Filtered Emission Lines")
                fig, ax = plt.subplots(figsize=(10, 5))
                # Plot all bars
                ax.bar(filtered_data["Wavelength(Å)"], filtered_data["luminosity(erg/s)"],width=1.0,
            color="blue",
            edgecolor="black",      # Adds a visible outline
            linewidth=0.2,          # Controls thickness of bar edges
            alpha=0.7)        # Highlight and label only "O 3" and "O3bn"
                for _, row in filtered_data.iterrows():

                    if is_main_line(
                        row["Label"],
                        row["Wavelength(Å)"],
                        main_lines,
                        main_wavelengths
                    ):
                        ax.text(
                            row["Wavelength(Å)"],
                            row["luminosity(erg/s)"] + 0.1,
                            row["Label"],
                            fontsize=10,
                            color="red"
                        )

                    
                # Set the y-axis limits to match the user input range
                ax.set_ylim(0, max_luminosity)
                
                ax.set_title("Filtered Emission Line luminosities", fontsize=16)
                ax.set_xlabel("Wavelength (Å)", fontsize=14)
                ax.set_ylabel("Log(luminosity)", fontsize=14)
                ax.grid(axis="y", linestyle="--", alpha=0.6)
                st.pyplot(fig)

                # Option to download filtered data
                st.download_button(
                    label="Download Filtered Emission Line Data as CSV",
                    data=filtered_data.to_csv(index=False),
                    file_name=f"{uploaded_file.name}_filtered.csv",
                    mime="text/csv",key=f"download_{uploaded_file.name}"
                )
            else:
                st.write("No emission lines match the selected filters!")
        #--------------------GRAPH 3: ALL LINES------------------------------
            st.subheader("Full Emission Line luminosities")
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(
            wavelengths,
            luminosities,
            width=1.0,
            color="blue",
            edgecolor="black",   
            linewidth=0.2,       
            alpha=0.7)
            for wl, lum, label in zip(wavelengths, luminosities, labels):
                
                if is_main_line(
                    label,
                    wl,
                    main_lines,
                    main_wavelengths
                ):
                    ax.text(
                        wl,
                        lum + 0.1,
                        label,
                        fontsize=9,
                        color="red"
                    )

            if st.checkbox("log scale x axis",value=True,key=f"logscale_{uploaded_file.name}"):
                ax.set_xscale('log')
            ax.set_title("Full Emission Line luminosities", fontsize=16)
            ax.set_xlabel("Wavelength (Å)", fontsize=14)
            ax.set_ylabel("Log(luminosity) [erg/s]", fontsize=14)
            ax.grid(axis="y", linestyle="--", alpha=0.6)
            st.pyplot(fig)
