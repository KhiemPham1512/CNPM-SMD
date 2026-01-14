from marshmallow import Schema, fields


class UserRequestSchema(Schema):
    """Schema for creating a new user. Password is plain text - will be hashed by service."""
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)  # Never returned in response
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    status = fields.Str(required=False, load_default='active')


class UserResponseSchema(Schema):
    """Schema for user response. Password hash is NEVER exposed."""
    user_id = fields.Int(required=True)
    username = fields.Str(required=True)
    # password_hash removed - security: never expose password hash in API response
    full_name = fields.Str(required=True)
    email = fields.Email(required=True)
    status = fields.Str(required=True)
    created_at = fields.Raw(required=True)


class UserUpdateStatusSchema(Schema):
    status = fields.Str(required=True)


class RoleAssignmentSchema(Schema):
    """Schema for assigning roles to a user."""
    roles = fields.List(
        fields.Str(required=True),
        required=True,
        validate=lambda roles: all(r.upper() in ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT'] for r in roles),
        error_messages={
            'required': 'roles array is required',
            'invalid': 'All roles must be one of: ADMIN, LECTURER, HOD, AA, PRINCIPAL, STUDENT'
        }
    )

