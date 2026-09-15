import os
import json
import glob
from datetime import date

import pandas as pd
from lxml import etree


# =========================
# CONFIGURATION
# =========================

MEDA_ROOT = "mars2020_meda"
OUTPUT = "output"

os.makedirs(OUTPUT, exist_ok=True)


# =========================
# 1. SENSOR METADATA
# =========================

def extract_sensor_metadata():

    bundle = os.path.join(
        MEDA_ROOT,
        "bundle.xml"
    )

    result = {
        "instrument": "Mars Environmental Dynamics Analyzer",
        "mission": "Mars 2020 Perseverance Rover",
        "source": "NASA PDS Mars 2020 MEDA Bundle",
        "doi": "10.17189/1522849"
    }


    if os.path.exists(bundle):

        try:
            tree = etree.parse(bundle)

            text = " ".join(
                tree.xpath(
                    "//*[text()]/text()"
                )
            )

            result["xml_parsed"] = True

            result["metadata_found"] = [
                x for x in
                [
                    "Mars",
                    "MEDA",
                    "Atmosphere",
                    "Meteorology"
                ]
                if x in text
            ]

        except Exception as e:

            result["xml_error"] = str(e)


    save(
        "sensor_specs.json",
        result
    )



# =========================
# 2. THERMAL EXTRACTION
# =========================

def extract_temperature():

    records = []


    paths = [

        os.path.join(
            MEDA_ROOT,
            "data_calibrated_env"
        ),

        os.path.join(
            MEDA_ROOT,
            "data_derived_env"
        )

    ]


    csv_files=[]


    for p in paths:

        csv_files.extend(
            glob.glob(
                p + "/**/*.csv",
                recursive=True
            )
        )


    print(
        "CSV files found:",
        len(csv_files)
    )


    for file in csv_files:

        try:

            df = pd.read_csv(
                file
            )


            for col in df.columns:

                name = col.lower()


                if (
                    "temp" in name
                    or
                    "temperature" in name
                    or
                    "thermal" in name
                ):


                    values = pd.to_numeric(
                        df[col],
                        errors="coerce"
                    ).dropna()


                    if len(values)>0:

                        records.append({

                            "file":
                            file.replace("\\","/"),

                            "column":
                            col,

                            "min_temp":
                            float(values.min()),

                            "max_temp":
                            float(values.max()),

                            "mean_temp":
                            float(values.mean()),

                            "std_dev":
                            float(values.std()),

                            "samples":
                            int(len(values))

                        })


        except Exception as e:

            print(
                "Skipped:",
                file,
                e
            )


    output={

        "dataset":
        "Mars 2020 MEDA Thermal Constraints",

        "source":
        "NASA PDS Mars 2020 MEDA Bundle",

        "processing":
        "Statistical extraction from calibrated and derived CSV products",

        "extraction_date":
        str(date.today()),

        "records":
        records
    }


    save(
        "thermal_constraints.json",
        output
    )



# =========================
# 3. DERIVED ENVIRONMENT MODEL
# =========================

def extract_environment_model():

    files = glob.glob(

        os.path.join(
            MEDA_ROOT,
            "data_derived_env",
            "**",
            "*.csv"
        ),

        recursive=True

    )


    model=[]


    for file in files:

        try:

            df=pd.read_csv(file)


            model.append({

                "file":
                file.replace("\\","/"),

                "columns":
                list(df.columns),

                "rows":
                len(df)

            })


        except:

            pass



    output={

        "dataset":
        "Mars 2020 MEDA Derived Environmental Data",

        "source":
        "NASA PDS Mars 2020 MEDA Derived Environmental Data",

        "processing":
        "CSV metadata extraction",

        "records":
        model

    }


    save(
        "environment_model.json",
        output
    )



# =========================
# 4. SOURCE DOCUMENTATION
# =========================

def create_sources():

    sources={

        "sensor_specs.json":{

            "source":
            "NASA PDS Mars 2020 MEDA bundle.xml",

            "processing":
            "XML metadata extraction"

        },


        "thermal_constraints.json":{

            "source":
            "NASA PDS Mars 2020 MEDA Calibrated Environmental Data",

            "processing":
            "Temperature statistical extraction"

        },


        "environment_model.json":{

            "source":
            "NASA PDS Mars 2020 MEDA Derived Environmental Data",

            "processing":
            "Derived CSV metadata extraction"

        }

    }


    save(
        "sources.json",
        sources
    )



# =========================
# SAVE FUNCTION
# =========================

def save(filename,data):

    path=os.path.join(
        OUTPUT,
        filename
    )


    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )


    print(
        "Created:",
        path
    )



# =========================
# MAIN
# =========================

if __name__=="__main__":


    print(
        "\nCINT-70 MEDA Extraction Started\n"
    )


    extract_sensor_metadata()

    extract_temperature()

    extract_environment_model()

    create_sources()


    print(
        "\nDONE - MEDA dataset processed"
    )