import { 
  TrendingUpIcon, 
  TrendingDownIcon, 
  MinusIcon 
} from '@heroicons/react/24/outline'

export default function KPICard({ 
  title, 
  value, 
  icon: Icon, 
  trend = 'neutral', 
  description,
  change 
}) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'positive':
        return <TrendingUpIcon className="h-4 w-4 text-success-500" />
      case 'negative':
        return <TrendingDownIcon className="h-4 w-4 text-danger-500" />
      default:
        return <MinusIcon className="h-4 w-4 text-gray-400" />
    }
  }

  const getTrendColor = () => {
    switch (trend) {
      case 'positive':
        return 'text-success-600'
      case 'negative':
        return 'text-danger-600'
      default:
        return 'text-gray-600'
    }
  }

  const getBorderColor = () => {
    switch (trend) {
      case 'positive':
        return 'border-l-success-500'
      case 'negative':
        return 'border-l-danger-500'
      default:
        return 'border-l-primary-500'
    }
  }

  return (
    <div className={`bg-white overflow-hidden shadow rounded-lg border-l-4 ${getBorderColor()}`}>
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <Icon className="h-6 w-6 text-gray-400" />
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-2xl font-semibold text-gray-900">
                  {value}
                </div>
                {change && (
                  <div className="ml-2 flex items-baseline text-sm">
                    {getTrendIcon()}
                    <span className={`ml-1 ${getTrendColor()}`}>
                      {change}
                    </span>
                  </div>
                )}
              </dd>
              {description && (
                <dd className="text-sm text-gray-500 mt-1">
                  {description}
                </dd>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
