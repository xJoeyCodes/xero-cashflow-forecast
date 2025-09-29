import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  ComposedChart
} from 'recharts'
import { format, parseISO } from 'date-fns'

export default function CashFlowChart({ data = [], height = 300 }) {
  // Transform data for chart
  const chartData = data.map(item => ({
    date: item.date,
    balance: item.predicted_cash_balance,
    income: item.predicted_income || 0,
    expenses: Math.abs(item.predicted_expenses || 0),
    lowerBound: item.confidence_interval_lower,
    upperBound: item.confidence_interval_upper,
    formattedDate: format(parseISO(item.date), 'MMM dd')
  }))

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (!chartData.length) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <div className="text-center">
          <div className="text-lg mb-2">📊</div>
          <div>No forecast data available</div>
          <div className="text-sm mt-1">Generate a forecast to see projections</div>
        </div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis 
          dataKey="formattedDate" 
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
        />
        <YAxis 
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          tickFormatter={formatCurrency}
        />
        <Tooltip content={<CustomTooltip />} />
        
        {/* Confidence interval area */}
        {chartData.some(d => d.lowerBound !== undefined) && (
          <Area
            dataKey="upperBound"
            stackId="confidence"
            stroke="none"
            fill="#3b82f6"
            fillOpacity={0.1}
          />
        )}
        {chartData.some(d => d.lowerBound !== undefined) && (
          <Area
            dataKey="lowerBound"
            stackId="confidence"
            stroke="none"
            fill="#ffffff"
            fillOpacity={1}
          />
        )}
        
        {/* Main cash flow line */}
        <Line
          type="monotone"
          dataKey="balance"
          stroke="#3b82f6"
          strokeWidth={3}
          dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
          name="Cash Balance"
        />
        
        {/* Income line */}
        <Line
          type="monotone"
          dataKey="income"
          stroke="#22c55e"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="Daily Income"
        />
        
        {/* Expenses line */}
        <Line
          type="monotone"
          dataKey="expenses"
          stroke="#ef4444"
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={false}
          name="Daily Expenses"
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
