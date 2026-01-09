from marshmallow import Schema, fields


class SyllabusCreateSchema(Schema):
    subject_id = fields.Int(required=True)
    program_id = fields.Int(required=True)
    owner_lecturer_id = fields.Int(required=True)


class SyllabusUpdateSchema(Schema):
    subject_id = fields.Int(required=False)
    program_id = fields.Int(required=False)
    owner_lecturer_id = fields.Int(required=False)


class SyllabusResponseSchema(Schema):
    syllabus_id = fields.Int(required=True)
    subject_id = fields.Int(required=True)
    program_id = fields.Int(required=True)
    owner_lecturer_id = fields.Int(required=True)
    current_version_id = fields.Int(required=False, allow_none=True)
    lifecycle_status = fields.Str(required=True)
    created_at = fields.Raw(required=True)

