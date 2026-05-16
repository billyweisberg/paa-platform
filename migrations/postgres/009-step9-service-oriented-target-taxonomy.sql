-- Project for Autonomous Agents
-- Step 9 Postgres DDL: service-oriented component element and realization taxonomy extension
--
-- Purpose:
-- - extend the top-level component element taxonomy where the proof slice exposed a gap
-- - extend the code-artifact realization taxonomy for service-oriented implementation slices
-- - add the allowed mappings needed to express service slices without overloading
--   repository-shaped realization kinds
--
-- Prerequisites:
-- - 007-step7-component-elements.sql
-- - 008-step8-component-element-realizations.sql

BEGIN;

CREATE SCHEMA IF NOT EXISTS paa;

INSERT INTO paa.component_element_types (
  element_key,
  label,
  category,
  description,
  is_brief_targetable,
  is_multi_instance,
  sort_order,
  metadata_json
)
VALUES (
  'verification_surfaces',
  'Verification Surfaces',
  'verification',
  'Test and proving surfaces that validate component behavior and protect architectural boundaries.',
  true,
  true,
  145,
  '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb
)
ON CONFLICT (element_key) DO UPDATE SET
  label = EXCLUDED.label,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_brief_targetable = EXCLUDED.is_brief_targetable,
  is_multi_instance = EXCLUDED.is_multi_instance,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();

INSERT INTO paa.component_element_realization_types (
  realization_key,
  label,
  category,
  description,
  is_brief_targetable,
  is_multi_instance,
  sort_order,
  metadata_json
)
VALUES
  ('service_interface', 'Service Interface', 'code_artifact', 'Abstract service contract or protocol defining supported planning operations.', true, false, 15, '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb),
  ('service_implementation', 'Service Implementation', 'code_artifact', 'Concrete default service class implementing the service interface and planning behavior.', true, false, 25, '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb),
  ('test_module', 'Test Module', 'verification_artifact', 'Concrete unit-test module or proving surface that validates the component slice.', true, true, 65, '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb),
  ('package_export', 'Package Export', 'code_artifact', 'Concrete package-surface export artifact such as an __init__ surface or public export binding.', true, true, 75, '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb)
ON CONFLICT (realization_key) DO UPDATE SET
  label = EXCLUDED.label,
  category = EXCLUDED.category,
  description = EXCLUDED.description,
  is_brief_targetable = EXCLUDED.is_brief_targetable,
  is_multi_instance = EXCLUDED.is_multi_instance,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json,
  updated_at = now();

INSERT INTO paa.component_element_type_realization_types (
  component_element_type_id,
  component_element_realization_type_id,
  is_default,
  sort_order,
  metadata_json
)
SELECT cet.component_element_type_id,
       cert.component_element_realization_type_id,
       m.is_default,
       m.sort_order,
       '{"taxonomy_extension": "service_oriented_slices", "source": "priority0-item2"}'::jsonb
FROM (
  VALUES
    ('interfaces', 'service_interface', false, 15),
    ('functions', 'service_implementation', false, 25),
    ('service_contract', 'service_interface', false, 55),
    ('verification_surfaces', 'test_module', true, 65),
    ('interfaces', 'package_export', false, 95)
) AS m(element_key, realization_key, is_default, sort_order)
JOIN paa.component_element_types cet
  ON cet.element_key = m.element_key
JOIN paa.component_element_realization_types cert
  ON cert.realization_key = m.realization_key
ON CONFLICT (component_element_type_id, component_element_realization_type_id) DO UPDATE SET
  is_default = EXCLUDED.is_default,
  sort_order = EXCLUDED.sort_order,
  metadata_json = EXCLUDED.metadata_json;

COMMIT;
