# Input Data Specifications: Automotive HLD Dataset

This directory contains the authentic and synthetic automotive High-Level Design (HLD) specifications utilized for ingestion, indexing, and evaluation in the Automotive Engineering AI Assistant platform.

## Dataset Files:
1. **`AUTOSAR_Powertrain_Master_HLD_110Pages.pdf` (110 Pages)**
   - **Domain:** Powertrain Domain Architecture
   - **Content:** Comprehensive enterprise ECU specification including 20 Application Software Components (SWCs), CAN-FD message matrix, torque monitoring safety goals (ISO 26262 ASIL-D), UDS diagnostics (ISO 14229), and memory mapping.
   - **Purpose:** Primary large-document stress testing and retrieval benchmark (100+ pages requirement).

2. **`AUTOSAR_Powertrain_Domain_HLD_v1.0.pdf` (20 Pages)**
   - **Domain:** Powertrain Subsystem Release 1.0
   - **Purpose:** Base architecture document used for automated revision diffing and port consistency audits.

3. **`AUTOSAR_Powertrain_Domain_HLD_v2.0.pdf` (22 Pages)**
   - **Domain:** Powertrain Subsystem Release 2.0
   - **Purpose:** Modified release containing updated cycle times, modified ASIL ratings, and additional regenerative braking SWCs to validate the Revision Comparator module.

4. **`AUTOSAR_Body_Gateway_HLD_v1.0.pdf` (15 Pages)**
   - **Domain:** Body & Comfort Gateway
   - **Purpose:** Cross-ECU domain evaluation (BCM, door controllers, lighting, and gateway routing).
