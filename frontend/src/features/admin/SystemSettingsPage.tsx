import { useEffect, useState } from 'react'
import { adminService } from '../../services/adminService'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'

export function SystemSettingsPage() {
  const [settings, setSettings] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminService.getSystemSettings()
      setSettings(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load system settings')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      await adminService.updateSystemSettings(settings)
      setSuccess('System settings updated successfully')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update system settings')
    } finally {
      setSaving(false)
    }
  }

  const handleChange = (key: string, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mb-4"></div>
          <p className="text-gray-500">Loading system settings...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">System Settings</h1>
          <p className="text-gray-600">Configure system parameters</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700">
          {success}
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
        <div className="space-y-6">
          <div>
            <Input
              label="FILE_STORAGE_ENABLED"
              type="text"
              value={settings.FILE_STORAGE_ENABLED || 'false'}
              onChange={(e) => handleChange('FILE_STORAGE_ENABLED', e.target.value)}
              placeholder="true or false"
            />
            <p className="mt-1 text-sm text-gray-500">
              Enable or disable file storage feature. Set to "true" to enable, "false" to disable.
            </p>
          </div>

          <div>
            <Input
              label="ACADEMIC_YEAR"
              type="text"
              value={settings.ACADEMIC_YEAR || ''}
              onChange={(e) => handleChange('ACADEMIC_YEAR', e.target.value)}
              placeholder="2024-2025"
            />
            <p className="mt-1 text-sm text-gray-500">
              Current academic year (e.g., "2024-2025").
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-yellow-800">
            <p className="font-medium mb-2">Note:</p>
            <p className="text-sm">
              System settings are stored in the database. Changes may require application restart to take full effect.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
