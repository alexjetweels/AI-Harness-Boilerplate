import React from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import ExecutePage from './pages/Execute';
import PipelinePage from './pages/Pipeline';
import './styles.css';

createRoot(document.getElementById('root')).render(
  <HashRouter>
    <Routes>
      <Route path="/"                  element={<Dashboard />} />
      <Route path="/execute"           element={<ExecutePage />} />
      <Route path="/pipeline/:runId"   element={<PipelinePage />} />
      <Route path="*"                  element={<Navigate to="/" replace />} />
    </Routes>
  </HashRouter>,
);
