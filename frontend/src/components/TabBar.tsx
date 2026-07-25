import type { Tab } from '../App'

interface TabBarProps {
  activeTab: Tab
  onTabChange: (tab: Tab) => void
  cleanCount: number
  flaggedCount: number
}

export default function TabBar({ activeTab, onTabChange, cleanCount, flaggedCount }: TabBarProps) {
  const tabs: { id: Tab; label: string; count: number }[] = [
    { id: 'clean', label: 'Clean Photos', count: cleanCount },
    { id: 'flagged', label: 'Flagged Photos', count: flaggedCount },
    { id: 'retouch', label: 'Color Retouch', count: 0 },
  ]

  return (
    <div className="flex gap-1 bg-surface-800 rounded-xl p-1 border border-surface-600">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          className={`
            flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium
            transition-all duration-150
            ${
              activeTab === tab.id
                ? 'bg-accent text-white shadow-lg shadow-accent/20'
                : 'text-gray-400 hover:text-gray-200 hover:bg-surface-600/50'
            }
          `}
        >
          {tab.label}
          {tab.count > 0 && (
            <span
              className={`text-xs px-2 py-0.5 rounded-full ${
                activeTab === tab.id
                  ? 'bg-white/20 text-white'
                  : tab.id === 'flagged'
                  ? 'bg-negative/20 text-negative'
                  : 'bg-positive/20 text-positive'
              }`}
            >
              {tab.count}
            </span>
          )}
        </button>
      ))}
    </div>
  )
}
