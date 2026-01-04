import type { Knex } from 'knex'

const tableName = 'elements_queryable'

export async function up(knex: Knex): Promise<void> {
  await knex.schema.createTable(tableName, (table) => {
    // Primary key - composite of stream_id and element_id
    table.text('element_id').notNullable()
    table.string('stream_id', 10).notNullable()

    // Hierarchy flattened (no joins needed!)
    table.string('project_id', 10).notNullable()
    table.text('project_name')
    table.string('model_id', 10)
    table.text('model_name')
    table.string('version_id', 10)
    table.text('version_message')
    table.text('root_object_id')

    // Top-level object fields
    table.string('speckle_type', 1024)
    table.timestamp('created_at', { precision: 3, useTz: true })
    table.integer('total_children_count')

    // Extracted JSONB fields (indexed!)
    table.string('ifc_type', 100)
    table.text('element_name')
    table.string('material', 255)
    table.string('building_storey', 255)
    table.string('tag', 255)

    // Revit fields
    table.string('revit_type', 255)
    table.string('revit_family', 255)
    table.string('revit_category', 255)
    table.string('revit_material', 255)

    // Quantities (extracted)
    table.decimal('volume', 20, 6)
    table.decimal('length', 20, 6)
    table.decimal('width', 20, 6)
    table.decimal('height', 20, 6)
    table.decimal('area', 20, 6)
    table.string('level', 255)

    // Full JSONB data (for detailed access)
    table.jsonb('full_data')

    // Metadata
    table
      .timestamp('last_updated', { precision: 3, useTz: true })
      .notNullable()
      .defaultTo(knex.fn.now())

    // Composite primary key
    table.primary(['stream_id', 'element_id'])
  })

  // Comprehensive indexes for fast queries
  await knex.schema.raw(`
    CREATE INDEX idx_elements_project ON ${tableName}(project_id);
    CREATE INDEX idx_elements_model ON ${tableName}(model_id);
    CREATE INDEX idx_elements_ifc_type ON ${tableName}(ifc_type);
    CREATE INDEX idx_elements_material ON ${tableName}(material);
    CREATE INDEX idx_elements_storey ON ${tableName}(building_storey);
    CREATE INDEX idx_elements_level ON ${tableName}(level);
    CREATE INDEX idx_elements_volume ON ${tableName}(volume);
    CREATE INDEX idx_elements_stream ON ${tableName}(stream_id);
    CREATE INDEX idx_elements_composite ON ${tableName}(project_id, ifc_type, material);
    
    -- GIN index on full_data for complex JSON queries
    CREATE INDEX idx_elements_data_gin ON ${tableName} USING GIN (full_data);
  `)
}

export async function down(knex: Knex): Promise<void> {
  await knex.schema.dropTable(tableName)
}


