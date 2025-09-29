import { useState, useEffect } from 'react'
import { 
  BanknotesIcon, 
  TrendingUpIcon, 
  TrendingDownIcon,
  CalendarDaysIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'
import CashFlowChart from '../components/CashFlowChart'
import ScenarioSimulator from '../components/ScenarioSimulator'
import KPICard from '../components/KPICard'
import { forecastService, transactionService } from '../services/api'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [forecastData, setForecastData] = useState([])
  const [summary, setSummary] = useState({})
  const [transactionSummary, setTransactionSummary] = useState({})

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      
      // Load forecast data
      const forecastResponse = await forecastService.getLatest({ days_ahead: 90 })
      setForecastData(forecastResponse.data.forecasts || [])
      setSummary(forecastResponse.data.summary || {})
      
      // Load transaction summary
      const transactionResponse = await transactionService.getSummary()
      setTransactionSummary(transactionResponse.data)
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateNewForecast = async () => {
    try {
      setLoading(true)
      await forecastService.generate({
        days_ahead: 90,
        model_type: 'prophet',
        include_confidence_intervals: true
      })
      await loadDashboardData()
    } catch (error) {
      console.error('Failed to generate forecast:', error)
      alert('Failed to generate forecast. Please try again.')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="loading-skeleton h-4 w-20 mb-2"></div>
                <div className="loading-skeleton h-8 w-24"></div>
              </div>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="loading-skeleton h-96 rounded-lg"></div>
          <div className="loading-skeleton h-96 rounded-lg"></div>
        </div>
      </div>
    )
  }

  const currentBalance = transactionSummary.net_cash_flow || 50000
  const projectedBalance = forecastData.length > 0 
    ? forecastData[forecastData.length - 1]?.predicted_cash_balance || currentBalance
    : currentBalance
  const cashRunwayDays = summary.cash_runway_days || 90
  const monthlyBurnRate = Math.abs(transactionSummary.total_expenses / 3) || 8000

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Cash Flow Dashboard
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Monitor your financial health and forecast future cash flow
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={generateNewForecast}
            className="btn-primary"
            disabled={loading}
          >
            <ChartBarIcon className="h-4 w-4 mr-2" />
            Refresh Forecast
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Current Balance"
          value={`$${currentBalance.toLocaleString()}`}
          icon={BanknotesIcon}
          trend={currentBalance > 0 ? 'positive' : 'negative'}
          description="Available cash"
        />
        <KPICard
          title="90-Day Projection"
          value={`$${projectedBalance.toLocaleString()}`}
          icon={TrendingUpIcon}
          trend={projectedBalance > currentBalance ? 'positive' : 'negative'}
          description="Forecasted balance"
        />
        <KPICard
          title="Cash Runway"
          value={`${cashRunwayDays} days`}
          icon={CalendarDaysIcon}
          trend={cashRunwayDays > 60 ? 'positive' : cashRunwayDays > 30 ? 'neutral' : 'negative'}
          description="Until cash runs out"
        />
        <KPICard
          title="Monthly Burn Rate"
          value={`$${monthlyBurnRate.toLocaleString()}`}
          icon={TrendingDownIcon}
          trend="neutral"
          description="Average monthly expenses"
        />
      </div>

      {/* Charts and Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Cash Flow Chart */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Cash Flow Forecast
          </h3>
          <CashFlowChart 
            data={forecastData} 
            height={300}
          />
        </div>

        {/* Scenario Simulator */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Scenario Simulator
          </h3>
          <ScenarioSimulator 
            onScenarioChange={(scenario) => {
              console.log('Scenario changed:', scenario)
            }}
          />
        </div>
      </div>

      {/* Recent Activity Summary */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Financial Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-success-50 rounded-lg">
            <div className="text-2xl font-bold text-success-600">
              ${(transactionSummary.total_income || 0).toLocaleString()}
            </div>
            <div className="text-sm text-success-700">Total Income</div>
          </div>
          <div className="text-center p-4 bg-danger-50 rounded-lg">
            <div className="text-2xl font-bold text-danger-600">
              ${Math.abs(transactionSummary.total_expenses || 0).toLocaleString()}
            </div>
            <div className="text-sm text-danger-700">Total Expenses</div>
          </div>
          <div className="text-center p-4 bg-primary-50 rounded-lg">
            <div className="text-2xl font-bold text-primary-600">
              ${(transactionSummary.net_cash_flow || 0).toLocaleString()}
            </div>
            <div className="text-sm text-primary-700">Net Cash Flow</div>
          </div>
        </div>
      </div>
    </div>
  )
}
