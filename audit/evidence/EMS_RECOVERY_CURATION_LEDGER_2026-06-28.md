# EMS Recovery Curation Ledger

RECOVERY_PROVENANCE:
LOCAL_WORKTREE_CONTENT_RECOVERY_NOT_GIT_HISTORY_RECOVERY

RAW_SOURCE_SNAPSHOT_SHA256:
8feaff20c1a5983e8f3c5f70878dcd222ae89cc9cf9ce906b6d0ae9c941fdbea

RAW_SOURCE_MANIFEST_STATUS:
IMMUTABLE_EXTERNAL_FORENSIC_RECORD

EMS_RAW_SOURCE_FIDELITY:
PASS_WITH_DECLARED_CURATION_DELTAS

UNEXPLAINED_MISMATCH_COUNT:
0

HASH_SEMANTICS:
- hash_algorithm: SHA-256
- hash_input: canonical_git_blob_content_bytes
- invalid_comparison_removed: GIT_OBJECT_ID_VS_SHA256_FILE_BYTES

CURATION_REASON_CATEGORIES:
- LINE_ENDING_ONLY
- TRANSPORT_MUTATION_REPAIRED
- LOCAL_PATH_REDACTION
- TEST_OUTPUT_ISOLATION
- LICENSE_GUARD_POLICY_ALIGNMENT
- RECOVERY_ASSURANCE_ARTIFACT_ADDED

CURATION_DELTAS:
- relative_path: .github/workflows/ems-local-guard.yml
  raw_source_sha256: bd3d2266fb02dfea89370c01b1c8b48a209dd500b267412737ab9c6f638cfae2
  curated_sha256: bd3d2266fb02dfea89370c01b1c8b48a209dd500b267412737ab9c6f638cfae2
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: .gitignore
  raw_source_sha256: cf481b8c23f9d3951b15efe69730e5ea57d8725f90e9d3a11b0fdfc511ef8353
  curated_sha256: cf481b8c23f9d3951b15efe69730e5ea57d8725f90e9d3a11b0fdfc511ef8353
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: LICENSE
  raw_source_sha256: NOT_IN_RAW_SOURCE
  curated_sha256: c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4
  raw_difference_type: NOT_IN_RAW_SOURCE
  curation_reason: LICENSE_GUARD_POLICY_ALIGNMENT
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: README.md
  raw_source_sha256: 5ac73fe4fec5a44740b1bf0364ee30ce3b1aec072b074596b2d4c0021a3f3967
  curated_sha256: 5ac73fe4fec5a44740b1bf0364ee30ce3b1aec072b074596b2d4c0021a3f3967
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: approvals/templates/ems_remote_push_approval_template.yaml
  raw_source_sha256: fb0d28ab6eb386b9566a2ef7f41e7ff1db7b76321e54d5fe8efb68b8ae2b203d
  curated_sha256: fb0d28ab6eb386b9566a2ef7f41e7ff1db7b76321e54d5fe8efb68b8ae2b203d
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/EMS_3H_REBUILD_REPORT.md
  raw_source_sha256: 84e2d1aa63c778c9298943c2542aca34b5847fb85f97da8dd72be9a3a2db1a8a
  curated_sha256: 84e2d1aa63c778c9298943c2542aca34b5847fb85f97da8dd72be9a3a2db1a8a
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/EMS_PHASE2_APPROVAL_PACKAGE_REPORT.md
  raw_source_sha256: 75edf7ff3248100368421539dfb1b155c203b38e31f4025d6870bd42d0e2776b
  curated_sha256: a3fbce9ebdddde6b68c514a0ef555b2e2cb2400fb706d4a3af88ff7205bc300b
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LOCAL_PATH_REDACTION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/EMS_RECOVERY_CURATION_LEDGER_2026-06-28.md
  raw_source_sha256: NOT_IN_RAW_SOURCE
  curated_sha256: RECORDED_IN_CURATED_MANIFEST
  raw_difference_type: NOT_IN_RAW_SOURCE
  curation_reason: RECOVERY_ASSURANCE_ARTIFACT_ADDED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_first_push_manifest.json
  raw_source_sha256: 0474ac64cbd41a4cc2dd8f462b6c7aa5035c098183e99623c61977e6302fb55e
  curated_sha256: 879e7570cbffdeecf07e07ff1b6229732530c79ca4da001fa1d0e6fe41b28e69
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LOCAL_PATH_REDACTION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_phase2_approval_validation.json
  raw_source_sha256: a4afb9094973a1583a589df6ed40fc2e39b239a2e72e553483cc47abc40a53b5
  curated_sha256: 8479a41a3c52d7ec45064b820fe93f7a5a1b9b42362d3f5fe240528f5a14ec4e
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LOCAL_PATH_REDACTION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_phase2_push_execution_plan.json
  raw_source_sha256: 1d6e6df7ad614ac281ba3f13e568f703afc7ddc4e04bfa04db5beccd022e1672
  curated_sha256: 1d6e6df7ad614ac281ba3f13e568f703afc7ddc4e04bfa04db5beccd022e1672
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_phase2_push_gate.json
  raw_source_sha256: 1b2466a6e642ee04d8b6556b6f1112bc5737769d01e109bd830fd89947b5d4a1
  curated_sha256: 840ed55c57a2927ec32505f04c1e1297764906fb4180d2c90baa332f60920eaa
  raw_difference_type: LINE_ENDING_ONLY
  curation_reason: TRANSPORT_MUTATION_REPAIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_rebuild_evidence.json
  raw_source_sha256: 3536b25f0e6cd0d583832805c33917c5a8f4526a0c213c77cd8409427a2600fb
  curated_sha256: d5d940f771ea99bbe2c09a93c1f1b9f33187de048b808a824b31d2b6a0f4265f
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LOCAL_PATH_REDACTION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/evidence/ems_recovery_curated_manifest_2026-06-28.json
  raw_source_sha256: NOT_IN_RAW_SOURCE
  curated_sha256: NOT_APPLICABLE_SELF_DESCRIBING_MANIFEST_EXCLUDED
  raw_difference_type: NOT_IN_RAW_SOURCE
  curation_reason: RECOVERY_ASSURANCE_ARTIFACT_ADDED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/score/ems_phase2_approval_score.json
  raw_source_sha256: c1b57e7359536d6886c5fb791b9dcdf8d68ed4a57fefb6322ac8272842f0158d
  curated_sha256: c1b57e7359536d6886c5fb791b9dcdf8d68ed4a57fefb6322ac8272842f0158d
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: audit/score/ems_rebuild_score.json
  raw_source_sha256: cc5f79f3f1b7d5c2ce1fbacc0a94f0a11bbec9f6441fa0e2b585f683e1486a8a
  curated_sha256: e560211f36a66a7ead0c9d6e5abae4a6a822c15955a02aeee090067b4bb7802f
  raw_difference_type: LINE_ENDING_ONLY
  curation_reason: TRANSPORT_MUTATION_REPAIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/__init__.py
  raw_source_sha256: 99b3d2c80b63c9b62aa285404aba3926e1c50536f62eb11c3364de3710ae5869
  curated_sha256: 99b3d2c80b63c9b62aa285404aba3926e1c50536f62eb11c3364de3710ae5869
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/api_contract.py
  raw_source_sha256: 59f8795814483f6f5abfb97ce7347b0523a6277f16af7db1c905ef068fa52685
  curated_sha256: 59f8795814483f6f5abfb97ce7347b0523a6277f16af7db1c905ef068fa52685
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/config.py
  raw_source_sha256: e0cef1080e22c40e8e8727c0952cba86173871e2d2c27ab80a035374cbde0c97
  curated_sha256: e0cef1080e22c40e8e8727c0952cba86173871e2d2c27ab80a035374cbde0c97
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/health.py
  raw_source_sha256: 697c42ee8939f55ba535e057e13ef3fbb72aacc42c3c757913039d59eb4196b0
  curated_sha256: 697c42ee8939f55ba535e057e13ef3fbb72aacc42c3c757913039d59eb4196b0
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/main.py
  raw_source_sha256: 9dd677ca22bda763a713f23ecdf097b2352739a1e14c7a02a59213939ebd68e8
  curated_sha256: 9dd677ca22bda763a713f23ecdf097b2352739a1e14c7a02a59213939ebd68e8
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/app/version.py
  raw_source_sha256: 7cb1794022f5d5f1cabdb7011aa078032985f04bf75bc19e3be3321f1739553c
  curated_sha256: 7cb1794022f5d5f1cabdb7011aa078032985f04bf75bc19e3be3321f1739553c
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/tests/conftest.py
  raw_source_sha256: a3ffb4ed295657966cbf09d0ffd067b5636d2ed40a21c5d9ec9aa97465d93394
  curated_sha256: a3ffb4ed295657966cbf09d0ffd067b5636d2ed40a21c5d9ec9aa97465d93394
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/tests/test_api_contract.py
  raw_source_sha256: 6b27c8a28102c59c4e7a360795609b8f21649c0ce2a0af50a729e690d8a4e242
  curated_sha256: 6b27c8a28102c59c4e7a360795609b8f21649c0ce2a0af50a729e690d8a4e242
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/tests/test_config.py
  raw_source_sha256: dddc74d4d35c7658ecef93880d1993cf0b0e3c6d41cb70f63d5157759bb2ed90
  curated_sha256: dddc74d4d35c7658ecef93880d1993cf0b0e3c6d41cb70f63d5157759bb2ed90
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: backend/tests/test_health.py
  raw_source_sha256: ce4887158ae8c6f4bcf026b10e9b7f31a594a57133ba80485d1b1e7c8ed95c29
  curated_sha256: ce4887158ae8c6f4bcf026b10e9b7f31a594a57133ba80485d1b1e7c8ed95c29
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: contracts/ems_api_contract.yaml
  raw_source_sha256: afa662d3758ba7db264224d84ca22d1d5a839e95e73cc3fadb4f045cb572d1f3
  curated_sha256: afa662d3758ba7db264224d84ca22d1d5a839e95e73cc3fadb4f045cb572d1f3
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: contracts/ems_port_matrix.yaml
  raw_source_sha256: 2b46ae6c11b17249986362dae9c94508c85d04962548a55e744f22a3bc1080e1
  curated_sha256: 2b46ae6c11b17249986362dae9c94508c85d04962548a55e744f22a3bc1080e1
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: contracts/ssid_core_integration_contract.yaml
  raw_source_sha256: 1b69c11fd39226853e60c0dc4782569e5372a88b9f93096f65d158984aea5539
  curated_sha256: 1b69c11fd39226853e60c0dc4782569e5372a88b9f93096f65d158984aea5539
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: docs/EMS_ARCHITECTURE.md
  raw_source_sha256: 604cd452fb2a20eeacdec43f72aea8fc873ebf400a436512e4477dd60f9c9e9e
  curated_sha256: 604cd452fb2a20eeacdec43f72aea8fc873ebf400a436512e4477dd60f9c9e9e
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: docs/EMS_LOCAL_REBUILD_RUNBOOK.md
  raw_source_sha256: 90a305c9dc606d5fbd47addb4f3bdf9cbe94ab7b718d0319dfa846800e9958c3
  curated_sha256: 90a305c9dc606d5fbd47addb4f3bdf9cbe94ab7b718d0319dfa846800e9958c3
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: docs/EMS_SECURITY_BOUNDARIES.md
  raw_source_sha256: 5cbe710f1a06faf53dbb8de1421109170f0dbd32ab4386474338631a80e9ccbe
  curated_sha256: 54d10cbe08a4cc798b97b060853ea9fc48672dd22ef649dda23550c1c2e44f05
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LOCAL_PATH_REDACTION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: frontend/src/App.tsx
  raw_source_sha256: 5e6beb515d79a94586f72bad8594e68b651697daa4ae1d79651dbadc92db6f14
  curated_sha256: 5e6beb515d79a94586f72bad8594e68b651697daa4ae1d79651dbadc92db6f14
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: frontend/src/config.ts
  raw_source_sha256: 8491a51e68bdfddba5151363fa1f39b557aa1f860a8d641838969d35303d83f3
  curated_sha256: 8491a51e68bdfddba5151363fa1f39b557aa1f860a8d641838969d35303d83f3
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: frontend/src/healthContract.ts
  raw_source_sha256: ab2c8c193b69c1d47f7cf1ed1e58192eaf619bd28f9bed82f6387169e6b4346a
  curated_sha256: ab2c8c193b69c1d47f7cf1ed1e58192eaf619bd28f9bed82f6387169e6b4346a
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: frontend/tests/healthContract.test.ts
  raw_source_sha256: 202e9da823a2d83bf99a2e0c56d06bfc792106971cc70eea8156fbed725b7f29
  curated_sha256: 202e9da823a2d83bf99a2e0c56d06bfc792106971cc70eea8156fbed725b7f29
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: registry/ems_contract_registry.yaml
  raw_source_sha256: 9bfe0fe3c174d9a03d1659e07b6c9faa8e8c4fc8de31e6a8cf687bdcb9fa412b
  curated_sha256: 9bfe0fe3c174d9a03d1659e07b6c9faa8e8c4fc8de31e6a8cf687bdcb9fa412b
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: registry/ems_module_registry.yaml
  raw_source_sha256: 0eba65c492906f2a66d8aa99c0c04f6a4593962ba249dfe79e0e3a411b799146
  curated_sha256: 0eba65c492906f2a66d8aa99c0c04f6a4593962ba249dfe79e0e3a411b799146
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: registry/ems_push_registry.yaml
  raw_source_sha256: f8c2c129db9dad15afebaa539e44a0eeb1cbe6e4f98c1173e926c268804c4290
  curated_sha256: f8c2c129db9dad15afebaa539e44a0eeb1cbe6e4f98c1173e926c268804c4290
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: registry/ems_remote_registry.yaml
  raw_source_sha256: c4c08d5e2e1c47a8af71caee363fcc35939ac98aacd76da2f2c3bcaa2969fed7
  curated_sha256: c4c08d5e2e1c47a8af71caee363fcc35939ac98aacd76da2f2c3bcaa2969fed7
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: schemas/ems_remote_push_approval.schema.json
  raw_source_sha256: 37640ecfe5257cfaca9d2f4a504cc491c870fcfd64adb14609cd46e974ef7c88
  curated_sha256: 37640ecfe5257cfaca9d2f4a504cc491c870fcfd64adb14609cd46e974ef7c88
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/ems_phase2_approval_validation.py
  raw_source_sha256: daa03f7d178e5afae7b25a3da197cab3c74343aeb58184d90b25ff1da1148ad1
  curated_sha256: b6fcabc5c1325e2cd865c4076b5847679178a830626c1e18e68ef9206ce41cb9
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/ems_push_gate.py
  raw_source_sha256: c263af131569a6a8091a674ffa264f29cdb46848ac78b18c30b73d541f7871f6
  curated_sha256: 7a951cab9d47dd30ac57103e9bee6c1f6d9b53cc28ba5ea1f0ab9c0498aa7b38
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/ems_score.py
  raw_source_sha256: 87850be516eba67fbbcfad4a2f5c817ad02f2b367e017b03035c50e83259f157
  curated_sha256: 10dcfdd912bc2255dbcad906c1fcf48173f1002953d7e7de3faac0e8181566ad
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/ems_static_guard.py
  raw_source_sha256: d6fe1254bfb008ebdc1e6f12462219618a226d52bc5453389940763cc47de409
  curated_sha256: 6c527a4455c8d9661f6736f188c2cb12a754b28632ce938f88d6850d1952d75e
  raw_difference_type: CONTENT_MUTATION
  curation_reason: LICENSE_GUARD_POLICY_ALIGNMENT
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/ems_validation.py
  raw_source_sha256: 81972ff08ad789d305163aa7e1c9e5d6f6b18eadb638fb394657a8ecfd9fb5e3
  curated_sha256: 4cbf3a4e8487df6c930ffd4a26ed3d80fd6abc29e6db1092ba66e2e8a301d867
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: scripts/first_push_manifest.py
  raw_source_sha256: 52d600e90846ee2ef224332e9c027d661cf25b14f6a7a2d52616a4ae5a599d98
  curated_sha256: 25bf2724b8935b9b4a16dd942ef80f854dc4e4c3818e930bca480d6474b37e9a
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/conftest.py
  raw_source_sha256: 7224232d6a56b0b01ac73ed05757f62ed01e4dbbf8a5385965b73d14a1427ff7
  curated_sha256: 7224232d6a56b0b01ac73ed05757f62ed01e4dbbf8a5385965b73d14a1427ff7
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/test_ems_push_gate.py
  raw_source_sha256: 7b9013ce14e0eff82bd5cfe45004a0044698b52702c428e4c0178626506d20f9
  curated_sha256: e4bed65ab6bd649e6d47bc991022290276a8677be1f8a412b1e1e54847ad24a7
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/test_ems_recovery_baseline_remediation.py
  raw_source_sha256: NOT_IN_RAW_SOURCE
  curated_sha256: 1f0a6f2968f0607d92bca4e91eb2a4f10f15be636fc08088445934383c8e92be
  raw_difference_type: NOT_IN_RAW_SOURCE
  curation_reason: RECOVERY_ASSURANCE_ARTIFACT_ADDED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/test_ems_score.py
  raw_source_sha256: 280cc7abae9df8cd0eb9ef85a6b7cd89eff4ec7372027e9b1ab41a623701044a
  curated_sha256: eff566f5a0f7d38c22cb1f30fc8f4de7d9388b354946f7b7a3e2172a8ef47dd6
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/test_ems_static_guard.py
  raw_source_sha256: c7dcc0b8ffd73e300531cc2dd17665dc23366ba40260c67c689a6fc972bc0abf
  curated_sha256: c7dcc0b8ffd73e300531cc2dd17665dc23366ba40260c67c689a6fc972bc0abf
  raw_difference_type: BYTE_IDENTICAL
  curation_reason: NO_CURATION_REQUIRED
  reviewed_at_utc: 2026-06-28T16:03:35Z
- relative_path: tests/test_first_push_manifest.py
  raw_source_sha256: daf04401a1f0d5bf864263fa5e6fb31f6d021cfc111f7cdc1803aaeaa16131f3
  curated_sha256: 404651dcff199cec3ee8fba000e3065e6a55b0a3d72a5bb7e663006ce260cea6
  raw_difference_type: CONTENT_MUTATION
  curation_reason: TEST_OUTPUT_ISOLATION
  reviewed_at_utc: 2026-06-28T16:03:35Z
