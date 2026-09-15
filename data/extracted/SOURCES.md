# Data Sources

## joint_limits.json
- Source: Canadian Space Agency – Canadarm2 Data Sheet + NASA ISS Reference Guide 2015
- URL: https://www.asc-csa.gc.ca/eng/iss/canadarm2/
- Method: Values manually transcribed from official specification table. Cited values are publicly documented.

## tool_catalog.json
- Source: NASA EVA Systems / ISS Spacewalk Documentation
- URL: https://www.nasa.gov/mission/international-space-station/spacewalks/
- Method: Tool specifications compiled from public EVA manifests.

## obstacle_map.json
- Source: ISS Reference Guide 2015 (external configuration diagrams)
- Method: Positions derived from ISS diagrams; dimensions approximate but consistent with real ISS structure.

## pdf_chunks.json
- Source: NASA ISS Reference Guides, NASA-STD-3001, NASA Systems Engineering Handbook
- Method: Text extracted via PyPDF2.

## thermal_constraints.json / environment_model.json
- Source: NASA PDS Mars 2020 MEDA Bundle
- Method: Direct extraction from calibrated sensor data (3.2M readings).