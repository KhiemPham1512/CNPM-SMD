import { useEffect, useState } from 'react'
import { useAuth } from '../../app/store/authContext'
import { userService } from '../../services/userService'
import { User } from '../../types'
import { Table } from '../../components/ui/Table'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Modal } from '../../components/ui/Modal'
import { Input } from '../../components/ui/Input'
import { Select } from '../../components/ui/Select'
import { ConfirmationModal } from '../../components/ui/ConfirmationModal'
import { formatDate } from '../../utils/date'
import { ConnectionDebug } from '../../components/debug/ConnectionDebug'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const createUserSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
  full_name: z.string().min(1, 'Full name is required'),
  email: z.string().email('Invalid email address'),
  status: z.enum(['active', 'inactive']).default('active'),
})

type CreateUserFormData = z.infer<typeof createUserSchema>

const roles = ['ADMIN', 'LECTURER', 'HOD', 'AA', 'PRINCIPAL', 'STUDENT'] as const

interface UserWithRoles extends User {
  roles?: string[]
}

export function UserManagementPage() {
  const { state } = useAuth()
  const [users, setUsers] = useState<UserWithRoles[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)
  const [isRemoveRoleModalOpen, setIsRemoveRoleModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [selectedRole, setSelectedRole] = useState<string>('')
  const [userRoles, setUserRoles] = useState<string[]>([])
  const [rolesLoading, setRolesLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [rolesMap, setRolesMap] = useState<Record<number, string[]>>({})

  const {
    register: registerCreate,
    handleSubmit: handleCreateSubmit,
    formState: { errors: createErrors },
    reset: resetCreateForm,
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      status: 'active',
    },
  })

  useEffect(() => {
    if (state.roles.includes('ADMIN')) {
      loadUsers()
    }
  }, [state.roles])

  const loadUsers = async () => {
    setError(null)
    setLoading(true)
    try {
      const data = await userService.list()
      setUsers(data)
      
      // Load roles for all users in parallel
      const rolesPromises = data.map(async (user) => {
        try {
          const roles = await userService.getUserRoles(user.user_id)
          return { userId: user.user_id, roles }
        } catch (err) {
          console.error(`Failed to load roles for user ${user.user_id}:`, err)
          return { userId: user.user_id, roles: [] }
        }
      })
      
      const rolesResults = await Promise.all(rolesPromises)
      const newRolesMap: Record<number, string[]> = {}
      rolesResults.forEach(({ userId, roles }) => {
        newRolesMap[userId] = roles
      })
      setRolesMap(newRolesMap)
    } catch (error) {
      console.error('Failed to load users:', error)
      let errorMessage = 'Failed to load users.'
      
      if (error instanceof Error) {
        errorMessage = error.message
        
        // Add more helpful debugging info
        if (errorMessage.includes('Cannot connect') || errorMessage.includes('Failed to fetch')) {
          errorMessage += `\n\nDebug info:\n- Frontend URL: ${window.location.origin}\n- Backend URL: ${import.meta.env.VITE_API_URL || 'http://localhost:9999'}\n- Check browser console (F12) for details`
        }
      }
      
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (data: CreateUserFormData) => {
    setProcessing(true)
    setError(null)
    try {
      await userService.create({
        username: data.username,
        password: data.password,
        full_name: data.full_name,
        email: data.email,
        status: data.status,
      })
      setIsCreateModalOpen(false)
      resetCreateForm()
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create user')
    } finally {
      setProcessing(false)
    }
  }

  const handleUpdateStatus = async (user: User, newStatus: string) => {
    setProcessing(true)
    setError(null)
    try {
      await userService.updateStatus(user.user_id, newStatus)
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update user status')
    } finally {
      setProcessing(false)
    }
  }

  const loadUserRoles = async (userId: number) => {
    setRolesLoading(true)
    try {
      const roles = await userService.getUserRoles(userId)
      setUserRoles(roles)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load user roles')
    } finally {
      setRolesLoading(false)
    }
  }

  const handleOpenRoleModal = async (user: User) => {
    setSelectedUser(user)
    setSelectedRole('')
    setIsRoleModalOpen(true)
    await loadUserRoles(user.user_id)
  }

  const handleAssignRole = async () => {
    if (!selectedUser || !selectedRole) return
    setProcessing(true)
    setError(null)
    try {
      await userService.assignRole(selectedUser.user_id, selectedRole)
      setSelectedRole('')
      await loadUserRoles(selectedUser.user_id)
      // Update roles map
      const updatedRoles = await userService.getUserRoles(selectedUser.user_id)
      setRolesMap(prev => ({ ...prev, [selectedUser.user_id]: updatedRoles }))
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to assign role')
    } finally {
      setProcessing(false)
    }
  }

  const handleRemoveRole = async (roleName: string) => {
    if (!selectedUser) return
    setProcessing(true)
    setError(null)
    try {
      await userService.removeRole(selectedUser.user_id, roleName)
      setIsRemoveRoleModalOpen(false)
      await loadUserRoles(selectedUser.user_id)
      // Update roles map
      const updatedRoles = await userService.getUserRoles(selectedUser.user_id)
      setRolesMap(prev => ({ ...prev, [selectedUser.user_id]: updatedRoles }))
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove role')
    } finally {
      setProcessing(false)
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return
    setProcessing(true)
    setError(null)
    try {
      await userService.delete(selectedUser.user_id)
      setIsDeleteModalOpen(false)
      setSelectedUser(null)
      await loadUsers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete user')
    } finally {
      setProcessing(false)
    }
  }

  if (!state.roles.includes('ADMIN')) {
    return <div className="text-gray-500">Access denied</div>
  }

  const columns = [
    { key: 'user_id', header: 'ID', accessor: (u: User) => u.user_id },
    { key: 'username', header: 'Username', accessor: (u: User) => u.username },
    { key: 'full_name', header: 'Name', accessor: (u: User) => u.full_name },
    { key: 'email', header: 'Email', accessor: (u: User) => u.email },
    {
      key: 'roles',
      header: 'Roles',
      render: (u: User) => {
        const roles = rolesMap[u.user_id] || []
        if (roles.length === 0) {
          return <span className="text-sm text-gray-400 italic">No roles</span>
        }
        return (
          <div className="flex flex-wrap gap-1">
            {roles.slice(0, 2).map(role => (
              <Badge key={role} variant="default" size="sm">
                {role}
              </Badge>
            ))}
            {roles.length > 2 && (
              <Badge variant="default" size="sm">
                +{roles.length - 2}
              </Badge>
            )}
          </div>
        )
      },
    },
    { 
      key: 'status', 
      header: 'Status', 
      render: (u: User) => (
        <div className="flex items-center gap-2">
          <Badge variant={u.status === 'active' ? 'success' : 'default'}>{u.status}</Badge>
          <select
            value={u.status}
            onChange={(e) => handleUpdateStatus(u, e.target.value)}
            className="text-sm px-2 py-1 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
            disabled={processing}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      )
    },
    { key: 'created_at', header: 'Created', accessor: (u: User) => formatDate(u.created_at) },
    {
      key: 'actions',
      header: 'Actions',
      render: (u: User) => (
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => handleOpenRoleModal(u)}
            disabled={processing}
          >
            Manage Roles
          </Button>
          <Button
            size="sm"
            variant="danger"
            onClick={() => {
              setSelectedUser(u)
              setIsDeleteModalOpen(true)
            }}
            disabled={processing}
          >
            Delete
          </Button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">User Management</h1>
          <p className="text-gray-600">Manage system users</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Create User
        </Button>
      </div>
      
      {error && (
        <>
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            <p className="font-semibold">Error loading users</p>
            <p className="text-sm mt-1 whitespace-pre-line">{error}</p>
            <div className="mt-3 flex gap-2">
              <button
                onClick={loadUsers}
                className="text-sm px-3 py-1 bg-red-100 hover:bg-red-200 rounded border border-red-300"
              >
                Try again
              </button>
              <button
                onClick={() => {
                  const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:9999'
                  window.open(`${backendUrl}/docs`, '_blank')
                }}
                className="text-sm px-3 py-1 bg-blue-100 hover:bg-blue-200 rounded border border-blue-300 text-blue-700"
              >
                Open Backend Docs
              </button>
            </div>
          </div>
          <ConnectionDebug />
        </>
      )}

      {loading ? (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
              <p className="text-gray-500">Loading users...</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
          {users.length === 0 && !error ? (
            <div className="text-center py-8 text-gray-500">
              <p className="mb-2">No users found.</p>
              <p className="text-sm">
                Make sure you have run the seed script: <code className="bg-gray-100 px-2 py-1 rounded">python -m scripts.seed_mvp</code>
              </p>
            </div>
          ) : (
            <Table columns={columns} data={users} />
          )}
        </div>
      )}

      {/* Create User Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false)
          resetCreateForm()
        }}
        title="Create User"
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsCreateModalOpen(false)
                resetCreateForm()
              }}
              disabled={processing}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateSubmit(handleCreateUser)}
              disabled={processing}
            >
              {processing ? 'Creating...' : 'Create User'}
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit(handleCreateUser)} className="space-y-6">
          <Input
            label="Username"
            type="text"
            placeholder="Enter username"
            error={createErrors.username?.message}
            {...registerCreate('username')}
          />

          <Input
            label="Password"
            type="password"
            placeholder="Enter password"
            error={createErrors.password?.message}
            {...registerCreate('password')}
          />

          <Input
            label="Full Name"
            type="text"
            placeholder="Enter full name"
            error={createErrors.full_name?.message}
            {...registerCreate('full_name')}
          />

          <Input
            label="Email"
            type="email"
            placeholder="Enter email"
            error={createErrors.email?.message}
            {...registerCreate('email')}
          />

          <div className="w-full">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              {...registerCreate('status')}
              className="w-full px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
            {createErrors.status && (
              <p className="mt-1 text-sm text-red-600">{createErrors.status.message}</p>
            )}
          </div>
        </form>
      </Modal>

      {/* Manage Roles Modal */}
      <Modal
        isOpen={isRoleModalOpen}
        onClose={() => {
          setIsRoleModalOpen(false)
          setSelectedUser(null)
          setSelectedRole('')
          setUserRoles([])
        }}
        title={`Manage Roles: ${selectedUser?.full_name || 'User'}`}
        footer={
          <>
            <Button
              variant="outline"
              onClick={() => {
                setIsRoleModalOpen(false)
                setSelectedUser(null)
                setSelectedRole('')
                setUserRoles([])
              }}
              disabled={processing}
            >
              Close
            </Button>
            <Button
              onClick={handleAssignRole}
              disabled={processing || !selectedRole}
            >
              {processing ? 'Assigning...' : 'Assign Role'}
            </Button>
          </>
        }
      >
        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">Current Roles</h3>
            {rolesLoading ? (
              <div className="text-sm text-gray-500">Loading roles...</div>
            ) : userRoles.length === 0 ? (
              <p className="text-sm text-gray-500">No roles assigned</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {userRoles.map(role => (
                  <div
                    key={role}
                    className="flex items-center gap-2 bg-primary-50 border border-primary-200 rounded-lg px-3 py-1.5"
                  >
                    <span className="text-sm font-medium text-primary-700">{role}</span>
                    <button
                      onClick={() => {
                        setSelectedRole(role)
                        setIsRemoveRoleModalOpen(true)
                      }}
                      className="text-primary-600 hover:text-primary-800 text-sm font-bold"
                      disabled={processing}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div>
            <Select
              label="Assign New Role"
              options={roles.map(role => ({ value: role, label: role }))}
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
            />
            <p className="text-sm text-gray-600 mt-2">
              Select a role to assign to this user.
            </p>
          </div>
        </div>
      </Modal>

      {/* Remove Role Confirmation Modal */}
      <ConfirmationModal
        isOpen={isRemoveRoleModalOpen}
        onClose={() => {
          setIsRemoveRoleModalOpen(false)
          setSelectedRole('')
        }}
        onConfirm={() => selectedRole && handleRemoveRole(selectedRole)}
        title="Remove Role"
        message={`Are you sure you want to remove the role "${selectedRole}" from ${selectedUser?.full_name || 'this user'}?`}
        confirmText="Remove"
        cancelText="Cancel"
        variant="danger"
        loading={processing}
      />

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false)
          setSelectedUser(null)
        }}
        onConfirm={handleDeleteUser}
        title="Delete User"
        message={`Are you sure you want to delete user "${selectedUser?.full_name || selectedUser?.username}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
        loading={processing}
      />
    </div>
  )
}
