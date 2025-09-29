import { useState, useEffect } from 'react'
import { simulationService } from '../services/api'
import { PlayIcon, ArrowPathIcon } from '@heroicons/react/24/outline'

export default function ScenarioSimulator({ onScenarioChange }) {
  const [parameters, setParameters] = useState({
    revenue_change_percent: 0,
    expense_change_percent: 0,
    one_time_income: 0,
    one_time_expense: 0,
    days_ahead: 90,
    scenario_name: 'Custom Scenario'
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [presets, setPresets] = useState([])

  useEffect(() => {
    loadPresets()
  }, [])

  const loadPresets = async () => {
    try {
      const response = await simulationService.getPresets()
      setPresets(response.data.presets || [])
    } catch (error) {
      console.error('Failed to load presets:', error)
    }
  }

  const runSimulation = async () => {
    try {
      setLoading(true)
      const response = await simulationService.run(parameters)
      setResult(response.data)
      onScenarioChange?.(response.data)
    } catch (error) {
      console.error('Simulation failed:', error)
      alert('Simulation failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const applyPreset = (preset) => {
    setParameters({
      ...parameters,
      ...preset.parameters
    })
  }

  const resetParameters = () => {
    setParameters({
      revenue_change_percent: 0,
      expense_change_percent: 0,
      one_time_income: 0,
      one_time_expense: 0,
      days_ahead: 90,
      scenario_name: 'Custom Scenario'
    })
    setResult(null)
  }

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="space-y-6">
      {/* Preset Scenarios */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Quick Scenarios
        </label>
        <div className="grid grid-cols-2 gap-2">
          {presets.slice(0, 4).map((preset, index) => (
            <button
              key={index}
              onClick={() => applyPreset(preset)}
              className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
              title={preset.description}
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      {/* Parameter Controls */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Revenue Change: {parameters.revenue_change_percent}%
          </label>
          <input
            type="range"
            min="-50"
            max="100"
            step="5"
            value={parameters.revenue_change_percent}
            onChange={(e) => setParameters({
              ...parameters,
              revenue_change_percent: parseFloat(e.target.value)
            })}
            className="scenario-slider"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>-50%</span>
            <span>+100%</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Expense Change: {parameters.expense_change_percent}%
          </label>
          <input
            type="range"
            min="-50"
            max="100"
            step="5"
            value={parameters.expense_change_percent}
            onChange={(e) => setParameters({
              ...parameters,
              expense_change_percent: parseFloat(e.target.value)
            })}
            className="scenario-slider"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>-50%</span>
            <span>+100%</span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="label">One-time Income</label>
            <input
              type="number"
              value={parameters.one_time_income}
              onChange={(e) => setParameters({
                ...parameters,
                one_time_income: parseFloat(e.target.value) || 0
              })}
              className="input"
              placeholder="0"
            />
          </div>
          <div>
            <label className="label">One-time Expense</label>
            <input
              type="number"
              value={parameters.one_time_expense}
              onChange={(e) => setParameters({
                ...parameters,
                one_time_expense: parseFloat(e.target.value) || 0
              })}
              className="input"
              placeholder="0"
            />
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex space-x-3">
        <button
          onClick={runSimulation}
          disabled={loading}
          className="btn-primary flex-1"
        >
          {loading ? (
            <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
          ) : (
            <PlayIcon className="h-4 w-4 mr-2" />
          )}
          Run Simulation
        </button>
        <button
          onClick={resetParameters}
          className="btn-secondary"
        >
          Reset
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-medium text-gray-900 mb-3">
            Simulation Results: {result.scenario_name}
          </h4>
          
          <div className="grid grid-cols-1 gap-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Final Cash Balance:</span>
              <span className="font-medium">
                {formatCurrency(result.summary.final_cash_balance)}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Net Cash Flow:</span>
              <span className={`font-medium ${
                result.summary.net_cash_flow >= 0 ? 'text-success-600' : 'text-danger-600'
              }`}>
                {formatCurrency(result.summary.net_cash_flow)}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-600">Cash Runway:</span>
              <span className="font-medium">
                {result.summary.cash_runway_days} days
              </span>
            </div>

            {result.comparison_with_baseline && (
              <div className="mt-3 pt-3 border-t border-gray-200">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-500">vs Baseline:</span>
                  <span className={`font-medium ${
                    result.comparison_with_baseline.improvement_percentage >= 0 
                      ? 'text-success-600' 
                      : 'text-danger-600'
                  }`}>
                    {result.comparison_with_baseline.improvement_percentage > 0 ? '+' : ''}
                    {result.comparison_with_baseline.improvement_percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
