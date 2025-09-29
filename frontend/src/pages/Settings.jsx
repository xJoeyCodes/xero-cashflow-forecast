import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import { 
  LinkIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  ArrowPathIcon,
  CogIcon
} from '@heroicons/react/24/outline'

export default function Settings() {
  const { user, connectXero, getXeroStatus, disconnectXero } = useAuth()
  const [xeroStatus, setXeroStatus] = useState({
    is_connected: false,
    is_token_valid: false,
    tenant_id: null,
    last_sync_at: null
  })
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)

  useEffect(() => {
    loadXeroStatus()
  }, [])

  const loadXeroStatus = async () => {
    try {
      setLoading(true)
      const status = await getXeroStatus()
      setXeroStatus(status)
    } catch (error) {
      console.error('Failed to load Xero status:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectXero = async () => {
    try {
      setConnecting(true)
      await connectXero()
    } catch (error) {
      console.error('Failed to connect to Xero:', error)
      alert('Failed to connect to Xero. Please try again.')
    } finally {
      setConnecting(false)
    }
  }

  const handleDisconnectXero = async () => {
    if (!confirm('Are you sure you want to disconnect from Xero?')) return

    try {
      const result = await disconnectXero()
      if (result.success) {
        setXeroStatus({
          is_connected: false,
          is_token_valid: false,
          tenant_id: null,
          last_sync_at: null
        })
        alert('Successfully disconnected from Xero')
      } else {
        alert('Failed to disconnect from Xero')
      }
    } catch (error) {
      console.error('Failed to disconnect from Xero:', error)
      alert('Failed to disconnect from Xero. Please try again.')
    }
  }

  const StatusIndicator = ({ isConnected, isValid }) => {
    if (isConnected && isValid) {
      return (
        <div className="flex items-center text-success-600">
          <CheckCircleIcon className="h-5 w-5 mr-2" />
          Connected & Active
        </div>
      )
    } else if (isConnected && !isValid) {
      return (
        <div className="flex items-center text-warning-600">
          <XCircleIcon className="h-5 w-5 mr-2" />
          Connected but Token Expired
        </div>
      )
    } else {
      return (
        <div className="flex items-center text-gray-500">
          <XCircleIcon className="h-5 w-5 mr-2" />
          Not Connected
        </div>
      )
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <div className="loading-skeleton h-6 w-32 mb-4"></div>
          <div className="loading-skeleton h-4 w-full mb-2"></div>
          <div className="loading-skeleton h-4 w-3/4"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Settings</h2>
        <p className="text-sm text-gray-600">
          Manage your account settings and integrations
        </p>
      </div>

      {/* Account Information */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Account Information</h3>
        </div>
        <div className="px-6 py-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <div className="mt-1 text-sm text-gray-900">{user?.email}</div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Account Status</label>
              <div className="mt-1">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                  Active
                </span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Member Since</label>
              <div className="mt-1 text-sm text-gray-900">
                {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Recently'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Xero Integration */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center">
            <CogIcon className="h-5 w-5 text-gray-400 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Xero Integration</h3>
          </div>
        </div>
        <div className="px-6 py-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection Status
              </label>
              <StatusIndicator 
                isConnected={xeroStatus.is_connected} 
                isValid={xeroStatus.is_token_valid} 
              />
            </div>

            {xeroStatus.tenant_id && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Tenant ID</label>
                <div className="mt-1 text-sm text-gray-900 font-mono">
                  {xeroStatus.tenant_id}
                </div>
              </div>
            )}

            {xeroStatus.last_sync_at && (
              <div>
                <label className="block text-sm font-medium text-gray-700">Last Sync</label>
                <div className="mt-1 text-sm text-gray-900">
                  {new Date(xeroStatus.last_sync_at).toLocaleString()}
                </div>
              </div>
            )}

            <div className="pt-4 border-t border-gray-200">
              {!xeroStatus.is_connected ? (
                <button
                  onClick={handleConnectXero}
                  disabled={connecting}
                  className="btn-primary"
                >
                  {connecting ? (
                    <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <LinkIcon className="h-4 w-4 mr-2" />
                  )}
                  Connect to Xero
                </button>
              ) : (
                <div className="flex space-x-3">
                  <button
                    onClick={handleConnectXero}
                    disabled={connecting}
                    className="btn-secondary"
                  >
                    <ArrowPathIcon className="h-4 w-4 mr-2" />
                    Reconnect
                  </button>
                  <button
                    onClick={handleDisconnectXero}
                    className="btn-danger"
                  >
                    Disconnect
                  </button>
                </div>
              )}
            </div>

            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h4 className="text-sm font-medium text-blue-900 mb-2">
                About Xero Integration
              </h4>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• Automatically sync your financial transactions</li>
                <li>• Import historical data for better forecasting</li>
                <li>• Real-time cash flow monitoring</li>
                <li>• Secure OAuth2.0 authentication</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Forecasting Settings */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Forecasting Preferences</h3>
        </div>
        <div className="px-6 py-4">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Default Forecast Period
              </label>
              <select className="input max-w-xs">
                <option value="30">30 days</option>
                <option value="60">60 days</option>
                <option value="90" selected>90 days</option>
                <option value="180">180 days</option>
                <option value="365">1 year</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Model
              </label>
              <select className="input max-w-xs">
                <option value="prophet" selected>Prophet (Recommended)</option>
                <option value="linear">Linear Regression</option>
                <option value="arima">ARIMA-like</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                id="confidence-intervals"
                type="checkbox"
                defaultChecked
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="confidence-intervals" className="ml-2 block text-sm text-gray-900">
                Include confidence intervals in forecasts
              </label>
            </div>

            <div className="flex items-center">
              <input
                id="auto-refresh"
                type="checkbox"
                defaultChecked
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <label htmlFor="auto-refresh" className="ml-2 block text-sm text-gray-900">
                Automatically refresh forecasts daily
              </label>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-200">
            <button className="btn-primary">
              Save Preferences
            </button>
          </div>
        </div>
      </div>

      {/* Data Management */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Data Management</h3>
        </div>
        <div className="px-6 py-4">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Clear Old Forecasts</h4>
                <p className="text-sm text-gray-500">Remove forecasts older than 30 days</p>
              </div>
              <button className="btn-secondary">Clear Data</button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Export Data</h4>
                <p className="text-sm text-gray-500">Download your transaction and forecast data</p>
              </div>
              <button className="btn-secondary">Export CSV</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
