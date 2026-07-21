import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { DocumentPage } from './pages/DocumentPage'
import { LibraryPage } from './pages/LibraryPage'
import { NewDocumentPage } from './pages/NewDocumentPage'
import { SystemPage } from './pages/SystemPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LibraryPage />} />
        <Route path="/new" element={<NewDocumentPage />} />
        <Route path="/documents/:number" element={<DocumentPage />} />
        <Route path="/system" element={<SystemPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
