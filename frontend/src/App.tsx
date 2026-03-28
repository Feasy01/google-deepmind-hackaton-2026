import { useState } from 'react'
import { Chat } from './components/Chat'
import { VoiceChat } from './components/VoiceChat'

type Tab = 'chat' | 'voice'

function App() {
  const [tab, setTab] = useState<Tab>('chat')

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <h1 className="text-xl font-semibold">DeepMind Assistant</h1>
          <nav className="flex gap-2">
            <button
              onClick={() => setTab('chat')}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                tab === 'chat'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              Text Chat
            </button>
            <button
              onClick={() => setTab('voice')}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                tab === 'voice'
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
              }`}
            >
              Voice Chat
            </button>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-3xl p-6">
        {tab === 'chat' ? <Chat /> : <VoiceChat />}
      </main>
    </div>
  )
}

export default App
