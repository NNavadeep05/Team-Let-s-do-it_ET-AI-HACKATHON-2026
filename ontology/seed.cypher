// ==========================================
// 1. Equipment Classes (ISO 14224 Level 6)
// ==========================================
MERGE (c1:EquipmentClass {id: "eq_cent_pump"}) SET c1.name = "Centrifugal Pump", c1.class_code = "PUMP-CF", c1.taxonomy_level = 6;
MERGE (c2:EquipmentClass {id: "eq_recip_pump"}) SET c2.name = "Reciprocating Pump", c2.class_code = "PUMP-RC", c2.taxonomy_level = 6;
MERGE (c3:EquipmentClass {id: "eq_rot_pump"}) SET c3.name = "Rotary Pump", c3.class_code = "PUMP-RT", c3.taxonomy_level = 6;
MERGE (c4:EquipmentClass {id: "eq_cent_comp"}) SET c4.name = "Centrifugal Compressor", c4.class_code = "COMP-CF", c4.taxonomy_level = 6;
MERGE (c5:EquipmentClass {id: "eq_recip_comp"}) SET c5.name = "Reciprocating Compressor", c5.class_code = "COMP-RC", c5.taxonomy_level = 6;
MERGE (c6:EquipmentClass {id: "eq_screw_comp"}) SET c6.name = "Screw Compressor", c6.class_code = "COMP-SC", c6.taxonomy_level = 6;
MERGE (c7:EquipmentClass {id: "eq_gas_turb"}) SET c7.name = "Gas Turbine", c7.class_code = "GTURB", c7.taxonomy_level = 6;
MERGE (c8:EquipmentClass {id: "eq_steam_turb"}) SET c8.name = "Steam Turbine", c8.class_code = "STURB", c8.taxonomy_level = 6;
MERGE (c9:EquipmentClass {id: "eq_ind_motor"}) SET c9.name = "Induction Motor", c9.class_code = "MOT-IND", c9.taxonomy_level = 6;
MERGE (c10:EquipmentClass {id: "eq_sync_motor"}) SET c10.name = "Synchronous Motor", c10.class_code = "MOT-SYN", c10.taxonomy_level = 6;
MERGE (c11:EquipmentClass {id: "eq_gate_valve"}) SET c11.name = "Gate Valve", c11.class_code = "VALV-GT", c11.taxonomy_level = 6;
MERGE (c12:EquipmentClass {id: "eq_globe_valve"}) SET c12.name = "Globe Valve", c12.class_code = "VALV-GL", c12.taxonomy_level = 6;
MERGE (c13:EquipmentClass {id: "eq_ball_valve"}) SET c13.name = "Ball Valve", c13.class_code = "VALV-BL", c13.taxonomy_level = 6;
MERGE (c14:EquipmentClass {id: "eq_check_valve"}) SET c14.name = "Check Valve", c14.class_code = "VALV-CK", c14.taxonomy_level = 6;
MERGE (c15:EquipmentClass {id: "eq_ctrl_valve"}) SET c15.name = "Control Valve", c15.class_code = "VALV-CT", c15.taxonomy_level = 6;
MERGE (c16:EquipmentClass {id: "eq_safety_valve"}) SET c16.name = "Safety/Relief Valve", c16.class_code = "VALV-SF", c16.taxonomy_level = 6;
MERGE (c17:EquipmentClass {id: "eq_shell_tube_hx"}) SET c17.name = "Shell & Tube Heat Exchanger", c17.class_code = "HX-ST", c17.taxonomy_level = 6;
MERGE (c18:EquipmentClass {id: "eq_plate_hx"}) SET c18.name = "Plate Heat Exchanger", c18.class_code = "HX-PL", c18.taxonomy_level = 6;
MERGE (c19:EquipmentClass {id: "eq_air_cooler"}) SET c19.name = "Air Cooler", c19.class_code = "HX-AC", c19.taxonomy_level = 6;
MERGE (c20:EquipmentClass {id: "eq_press_vessel"}) SET c20.name = "Pressure Vessel", c20.class_code = "VESSEL", c20.taxonomy_level = 6;
MERGE (c21:EquipmentClass {id: "eq_storage_tank"}) SET c21.name = "Storage Tank", c21.class_code = "TANK", c21.taxonomy_level = 6;
MERGE (c22:EquipmentClass {id: "eq_press_trans"}) SET c22.name = "Pressure Transmitter", c22.class_code = "INST-PT", c22.taxonomy_level = 6;
MERGE (c23:EquipmentClass {id: "eq_temp_trans"}) SET c23.name = "Temperature Transmitter", c23.class_code = "INST-TT", c23.taxonomy_level = 6;
MERGE (c24:EquipmentClass {id: "eq_flow_trans"}) SET c24.name = "Flow Transmitter", c24.class_code = "INST-FT", c24.taxonomy_level = 6;
MERGE (c25:EquipmentClass {id: "eq_level_trans"}) SET c25.name = "Level Transmitter", c25.class_code = "INST-LT", c25.taxonomy_level = 6;
MERGE (c26:EquipmentClass {id: "eq_vib_sensor"}) SET c26.name = "Vibration Sensor", c26.class_code = "INST-VT", c26.taxonomy_level = 6;
MERGE (c27:EquipmentClass {id: "eq_gas_detector"}) SET c27.name = "Gas Detector", c27.class_code = "INST-GD", c27.taxonomy_level = 6;
MERGE (c28:EquipmentClass {id: "eq_cent_fan"}) SET c28.name = "Centrifugal Fan/Blower", c28.class_code = "FAN-CF", c28.taxonomy_level = 6;
MERGE (c29:EquipmentClass {id: "eq_transformer"}) SET c29.name = "Power Transformer", c29.class_code = "ELEC-TR", c29.taxonomy_level = 6;
MERGE (c30:EquipmentClass {id: "eq_switchgear"}) SET c30.name = "Switchgear", c30.class_code = "ELEC-SG", c30.taxonomy_level = 6;

// ==========================================
// 2. Failure Modes (ISO 14224)
// ==========================================
MERGE (f1:FailureMode {id: "fm_seal_leak"}) SET f1.name = "External seal leakage", f1.mode_code = "ELK", f1.description = "Leakage of process medium through shaft seals or gasketed connections";
MERGE (f2:FailureMode {id: "fm_vib_high"}) SET f2.name = "Abnormal vibration", f2.mode_code = "VIB", f2.description = "High shaft or bearing housing vibration amplitudes";
MERGE (f3:FailureMode {id: "fm_temp_high"}) SET f3.name = "Overheating / High bearing temp", f3.mode_code = "OHT", f3.description = "High temperature in bearings or windings";
MERGE (f4:FailureMode {id: "fm_fail_start"}) SET f4.name = "Failure to start on demand", f4.mode_code = "FSTD", f4.description = "Driver or equipment fails to initiate operation";
MERGE (f5:FailureMode {id: "fm_fail_stop"}) SET f5.name = "Failure to stop on demand", f5.mode_code = "FSPD", f5.description = "Equipment fails to shut down on trigger";
MERGE (f6:FailureMode {id: "fm_loss_flow"}) SET f6.name = "Loss of flow / low output", f6.mode_code = "LFL", f6.description = "Insufficient discharge pressure or volume";
MERGE (f7:FailureMode {id: "fm_cavitation"}) SET f7.name = "Cavitation damage", f7.mode_code = "CAV", f7.description = "Vapor bubble implosion leading to mechanical erosion";
MERGE (f8:FailureMode {id: "fm_leak_body"}) SET f8.name = "Valve body/casing leak", f8.mode_code = "LKB", f8.description = "External leakage through casting defects or flange bolt fatigue";
MERGE (f9:FailureMode {id: "fm_fail_close"}) SET f9.name = "Fail to close / internal bypass", f9.mode_code = "FTC", f9.description = "Valve fails to seal completely when shut";
MERGE (f10:FailureMode {id: "fm_fail_open"}) SET f10.name = "Fail to open / blocked", f10.mode_code = "FTO", f10.description = "Valve fails to actuate to fully open position";
MERGE (f11:FailureMode {id: "fm_block_tube"}) SET f11.name = "Heat exchanger tube plugging", f11.mode_code = "PLG", f11.description = "Silt, scale, or biological fouling blocking flow paths";
MERGE (f12:FailureMode {id: "fm_inst_drift"}) SET f12.name = "Instrument signal drift", f12.mode_code = "DRFT", f12.description = "Calibration loss causing incorrect parameter transmission";
MERGE (f13:FailureMode {id: "fm_elec_short"}) SET f13.name = "Short circuit / insulation breakdown", f13.mode_code = "ELSC", f13.description = "Electrical grounding or phase failure in stator windings";

// Map typical failure modes to equipment classes
MATCH (c:EquipmentClass {id: "eq_cent_pump"}) MATCH (f:FailureMode {id: "fm_seal_leak"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_pump"}) MATCH (f:FailureMode {id: "fm_vib_high"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_pump"}) MATCH (f:FailureMode {id: "fm_loss_flow"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_pump"}) MATCH (f:FailureMode {id: "fm_cavitation"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_pump"}) MATCH (f:FailureMode {id: "fm_temp_high"}) MERGE (f)-[:TYPICAL_FOR]->(c);

MATCH (c:EquipmentClass {id: "eq_cent_comp"}) MATCH (f:FailureMode {id: "fm_vib_high"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_comp"}) MATCH (f:FailureMode {id: "fm_temp_high"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_cent_comp"}) MATCH (f:FailureMode {id: "fm_seal_leak"}) MERGE (f)-[:TYPICAL_FOR]->(c);

MATCH (c:EquipmentClass {id: "eq_ind_motor"}) MATCH (f:FailureMode {id: "fm_fail_start"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_ind_motor"}) MATCH (f:FailureMode {id: "fm_temp_high"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_ind_motor"}) MATCH (f:FailureMode {id: "fm_elec_short"}) MERGE (f)-[:TYPICAL_FOR]->(c);

MATCH (c:EquipmentClass {id: "eq_ctrl_valve"}) MATCH (f:FailureMode {id: "fm_fail_close"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_ctrl_valve"}) MATCH (f:FailureMode {id: "fm_fail_open"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_ctrl_valve"}) MATCH (f:FailureMode {id: "fm_seal_leak"}) MERGE (f)-[:TYPICAL_FOR]->(c);

MATCH (c:EquipmentClass {id: "eq_shell_tube_hx"}) MATCH (f:FailureMode {id: "fm_block_tube"}) MERGE (f)-[:TYPICAL_FOR]->(c);
MATCH (c:EquipmentClass {id: "eq_shell_tube_hx"}) MATCH (f:FailureMode {id: "fm_seal_leak"}) MERGE (f)-[:TYPICAL_FOR]->(c);

// ==========================================
// 3. Typical Causes
// ==========================================
MERGE (ca1:Cause {id: "ca_misalign"}) SET ca1.name = "Shaft Misalignment", ca1.category = "Mechanical";
MERGE (ca2:Cause {id: "ca_unbalance"}) SET ca2.name = "Rotor Unbalance", ca2.category = "Mechanical";
MERGE (ca3:Cause {id: "ca_lub_starve"}) SET ca3.name = "Lubricant Starvation", ca3.category = "Lubrication";
MERGE (ca4:Cause {id: "ca_wrong_lub"}) SET ca4.name = "Incorrect Viscosity / Lubricant Grade", ca4.category = "Lubrication";
MERGE (ca5:Cause {id: "ca_bolt_loose"}) SET ca5.name = "Flange / Bolt Loosening", ca5.category = "Mechanical";
MERGE (ca6:Cause {id: "ca_seal_wear"}) SET ca6.name = "Normal Wear of Elastomer Seals", ca6.category = "Wear";
MERGE (ca7:Cause {id: "ca_clog"}) SET ca7.name = "Particulate Clogging / Fouling", ca7.category = "Process";
MERGE (ca8:Cause {id: "ca_cav_flow"}) SET ca8.name = "Low Suction Head (NPSHA < NPSHR)", ca8.category = "Hydraulic";
MERGE (ca9:Cause {id: "ca_ins_break"}) SET ca9.name = "Thermal Overload / Insulating Ageing", ca9.category = "Electrical";

// Link Failure Modes to Causes
MATCH (f:FailureMode {id: "fm_seal_leak"}) MATCH (c:Cause {id: "ca_misalign"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_seal_leak"}) MATCH (c:Cause {id: "ca_seal_wear"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_seal_leak"}) MATCH (c:Cause {id: "ca_bolt_loose"}) MERGE (f)-[:CAUSED_BY]->(c);

MATCH (f:FailureMode {id: "fm_vib_high"}) MATCH (c:Cause {id: "ca_misalign"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_vib_high"}) MATCH (c:Cause {id: "ca_unbalance"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_vib_high"}) MATCH (c:Cause {id: "ca_cav_flow"}) MERGE (f)-[:CAUSED_BY]->(c);

MATCH (f:FailureMode {id: "fm_temp_high"}) MATCH (c:Cause {id: "ca_lub_starve"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_temp_high"}) MATCH (c:Cause {id: "ca_wrong_lub"}) MERGE (f)-[:CAUSED_BY]->(c);
MATCH (f:FailureMode {id: "fm_temp_high"}) MATCH (c:Cause {id: "ca_misalign"}) MERGE (f)-[:CAUSED_BY]->(c);

MATCH (f:FailureMode {id: "fm_cavitation"}) MATCH (c:Cause {id: "ca_cav_flow"}) MERGE (f)-[:CAUSED_BY]->(c);

// ==========================================
// 4. Typical Symptoms
// ==========================================
MERGE (s1:Symptom {id: "sym_vib_noise"}) SET s1.name = "Audible whine / vibration noise";
MERGE (s2:Symptom {id: "sym_oil_leak"}) SET s2.name = "Visible oil droplets on foundation";
MERGE (s3:Symptom {id: "sym_hiss"}) SET s3.name = "Hissing sound (escaping medium)";
MERGE (s4:Symptom {id: "sym_smoke"}) SET s4.name = "Smoke / hot electrical odour";
MERGE (s5:Symptom {id: "sym_low_press"}) SET s5.name = "Discharge pressure drop";

// Link Failure Modes to Symptoms
MATCH (f:FailureMode {id: "fm_seal_leak"}) MATCH (s:Symptom {id: "sym_oil_leak"}) MERGE (f)-[:MANIFESTS_AS]->(s);
MATCH (f:FailureMode {id: "fm_seal_leak"}) MATCH (s:Symptom {id: "sym_hiss"}) MERGE (f)-[:MANIFESTS_AS]->(s);

MATCH (f:FailureMode {id: "fm_vib_high"}) MATCH (s:Symptom {id: "sym_vib_noise"}) MERGE (f)-[:MANIFESTS_AS]->(s);
MATCH (f:FailureMode {id: "fm_temp_high"}) MATCH (s:Symptom {id: "sym_vib_noise"}) MERGE (f)-[:MANIFESTS_AS]->(s);

MATCH (f:FailureMode {id: "fm_elec_short"}) MATCH (s:Symptom {id: "sym_smoke"}) MERGE (f)-[:MANIFESTS_AS]->(s);
MATCH (f:FailureMode {id: "fm_loss_flow"}) MATCH (s:Symptom {id: "sym_low_press"}) MERGE (f)-[:MANIFESTS_AS]->(s);
