// Loan Timeline Component for React/Vite/TypeScript
// Shows comprehensive timeline view for any loan number

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8001';

interface TimelineEvent {
  orkuid: string;
  timestamp: string;
  duration: number;
  user_name?: string;
  summary: string;
  key_facts: Record<string, any>;
  sentiment?: string;
  loan_mentions: number;
}

interface LoanTimeline {
  loan_number: string;
  total_calls: number;
  total_duration_minutes: number;
  first_contact: string;
  last_contact: string;
  primary_user?: string;
  timeline_events: TimelineEvent[];
  aggregated_summary: string;
  key_milestones: Array<{
    date: string;
    type: string;
    description: string;
    orkuid: string;
    sentiment?: string;
  }>;
  sentiment_trend: Record<string, number>;
}

interface LoanInsights {
  loan_number: string;
  loan_status: string;
  key_issues: string[];
  action_items: string[];
  risk_indicators: string[];
  compliance_notes: string[];
}

export const LoanTimelineView: React.FC = () => {
  const [loanNumber, setLoanNumber] = useState('');
  const [timeline, setTimeline] = useState<LoanTimeline | null>(null);
  const [insights, setInsights] = useState<LoanInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<'timeline' | 'insights' | 'summary'>('timeline');

  const searchLoan = async () => {
    if (!loanNumber.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      // Fetch timeline
      const timelineResponse = await axios.get(`${API_BASE}/timeline/${loanNumber}`);
      setTimeline(timelineResponse.data);
      
      // Fetch insights
      const insightsResponse = await axios.get(`${API_BASE}/insights/${loanNumber}`);
      setInsights(insightsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load timeline');
      setTimeline(null);
      setInsights(null);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment?: string) => {
    switch (sentiment) {
      case 'positive': return '#10b981';
      case 'negative': return '#ef4444';
      case 'neutral': return '#6b7280';
      default: return '#9ca3af';
    }
  };

  const getStatusBadge = (status: string) => {
    const colors = {
      'Active': 'bg-blue-100 text-blue-800',
      'Resolved': 'bg-green-100 text-green-800',
      'At Risk': 'bg-red-100 text-red-800',
      'Denied': 'bg-gray-100 text-gray-800'
    };
    return colors[status as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Loan Timeline Analysis</h1>
      
      {/* Search Box */}
      <div className="mb-8 flex gap-4">
        <input
          type="text"
          value={loanNumber}
          onChange={(e) => setLoanNumber(e.target.value)}
          placeholder="Enter loan number..."
          className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyPress={(e) => e.key === 'Enter' && searchLoan()}
        />
        <button
          onClick={searchLoan}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {timeline && insights && (
        <div className="space-y-6">
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Status</div>
              <div className="mt-1">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(insights.loan_status)}`}>
                  {insights.loan_status}
                </span>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Total Calls</div>
              <div className="text-2xl font-bold">{timeline.total_calls}</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Total Duration</div>
              <div className="text-2xl font-bold">{timeline.total_duration_minutes} min</div>
            </div>
            
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Primary User</div>
              <div className="text-lg font-medium">{timeline.primary_user || 'Unknown'}</div>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {(['timeline', 'insights', 'summary'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="bg-white rounded-lg shadow p-6">
            {activeTab === 'timeline' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Call Timeline</h2>
                <div className="space-y-4">
                  {timeline.timeline_events.map((event, index) => (
                    <div key={event.orkuid} className="flex gap-4">
                      <div className="flex-shrink-0">
                        <div
                          className="w-3 h-3 rounded-full mt-1.5"
                          style={{ backgroundColor: getSentimentColor(event.sentiment) }}
                        />
                        {index < timeline.timeline_events.length - 1 && (
                          <div className="w-0.5 h-16 bg-gray-300 ml-1.25" />
                        )}
                      </div>
                      
                      <div className="flex-1 pb-8">
                        <div className="bg-gray-50 rounded-lg p-4">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <div className="font-medium">
                                {format(new Date(event.timestamp), 'MMM d, yyyy h:mm a')}
                              </div>
                              <div className="text-sm text-gray-500">
                                {event.user_name || 'Unknown'} • {Math.floor(event.duration / 60)}m call
                              </div>
                            </div>
                            <span
                              className="px-2 py-1 rounded text-xs"
                              style={{
                                backgroundColor: getSentimentColor(event.sentiment) + '20',
                                color: getSentimentColor(event.sentiment)
                              }}
                            >
                              {event.sentiment || 'unknown'}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700">{event.summary}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Key Milestones */}
                {timeline.key_milestones.length > 0 && (
                  <div className="mt-8">
                    <h3 className="text-lg font-semibold mb-4">Key Milestones</h3>
                    <div className="space-y-2">
                      {timeline.key_milestones.map((milestone, index) => (
                        <div key={index} className="flex items-center gap-4 p-3 bg-blue-50 rounded-lg">
                          <div className="font-medium text-blue-900">{milestone.type}</div>
                          <div className="text-sm text-blue-700">{milestone.description}</div>
                          <div className="text-sm text-blue-500 ml-auto">
                            {format(new Date(milestone.date), 'MMM d, yyyy')}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="space-y-6">
                <h2 className="text-xl font-semibold">AI-Powered Insights</h2>
                
                {insights.key_issues.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">Key Issues</h3>
                    <ul className="list-disc list-inside space-y-1">
                      {insights.key_issues.map((issue, index) => (
                        <li key={index} className="text-gray-700">{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {insights.action_items.length > 0 && (
                  <div>
                    <h3 className="font-medium mb-2">Action Items</h3>
                    <ul className="space-y-2">
                      {insights.action_items.map((item, index) => (
                        <li key={index} className="flex items-start gap-2">
                          <input type="checkbox" className="mt-1" />
                          <span className="text-gray-700">{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {insights.risk_indicators.length > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg">
                    <h3 className="font-medium text-red-900 mb-2">Risk Indicators</h3>
                    <ul className="space-y-1">
                      {insights.risk_indicators.map((risk, index) => (
                        <li key={index} className="text-red-700 text-sm">⚠️ {risk}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {insights.compliance_notes.length > 0 && (
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <h3 className="font-medium mb-2">Compliance Notes</h3>
                    <ul className="space-y-1">
                      {insights.compliance_notes.map((note, index) => (
                        <li key={index} className="text-gray-700 text-sm">✓ {note}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'summary' && (
              <div>
                <h2 className="text-xl font-semibold mb-4">Executive Summary</h2>
                <div className="prose max-w-none">
                  <p className="text-gray-700 whitespace-pre-line">{timeline.aggregated_summary}</p>
                  
                  <div className="mt-6 grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Timeline Range</h4>
                      <p className="text-sm text-gray-600">
                        {format(new Date(timeline.first_contact), 'MMM d, yyyy')} - {' '}
                        {format(new Date(timeline.last_contact), 'MMM d, yyyy')}
                      </p>
                    </div>
                    
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Sentiment Distribution</h4>
                      <div className="space-y-1">
                        {Object.entries(timeline.sentiment_trend).map(([sentiment, count]) => (
                          <div key={sentiment} className="flex justify-between text-sm">
                            <span className="capitalize">{sentiment}</span>
                            <span className="font-medium">{count} calls</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};