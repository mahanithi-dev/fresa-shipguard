import React from "react";
import { AlertTriangle, Boxes, CalendarClock, ShieldCheck } from "lucide-react";

export default function LandingPage({ onEnter }) {
  return (
    <main className="erp-landing">
      <header className="erp-header">
        <div className="erp-nav">
          <div className="erp-logo">
            <ShieldCheck size={28} />
            <span>ShipGuard</span>
          </div>
          <nav className="erp-nav-links">
            <a href="#solutions">Solutions</a>
            <a href="#features">Features</a>
            <a href="#about">About</a>
          </nav>
          <div className="erp-nav-actions">
            <button className="erp-secondary-btn" onClick={onEnter}>Sign In</button>
            <button className="erp-primary-btn" onClick={onEnter}>Enter ShipGuard</button>
          </div>
        </div>
      </header>

      <section className="erp-hero">
        <div className="erp-hero-content">
          <h1>Enterprise Shipment Risk Management</h1>
          <p className="erp-hero-subtitle">
            Predict delays, optimize operations, and reduce costs with AI-powered logistics intelligence. 
            Built for freight forwarders, logistics providers, and supply chain professionals.
          </p>
          <div className="erp-hero-stats">
            <div className="erp-stat">
              <strong>81%</strong>
              <span>Prediction Accuracy</span>
            </div>
            <div className="erp-stat">
              <strong>40%</strong>
              <span>Delay Reduction</span>
            </div>
            <div className="erp-stat">
              <strong>24/7</strong>
              <span>Real-time Monitoring</span>
            </div>
          </div>
          <div className="erp-hero-cta">
            <button className="erp-primary-btn large" onClick={onEnter}>
              Get Started
            </button>
            <button className="erp-secondary-btn large" onClick={onEnter}>
              Schedule Demo
            </button>
          </div>
        </div>
      </section>

      <section className="erp-trust" id="about">
        <div className="erp-trust-content">
          <h2>Trusted by Logistics Professionals</h2>
          <p>ShipGuard helps leading freight forwarding companies manage shipment risks and improve operational efficiency.</p>
        </div>
      </section>

      <section className="erp-solutions" id="solutions">
        <div className="erp-section-header">
          <h2>Solutions for Every Logistics Challenge</h2>
          <p>Comprehensive risk management platform designed for modern supply chain operations</p>
        </div>
        <div className="erp-solutions-grid">
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <AlertTriangle size={32} />
            </div>
            <h3>Risk Prediction</h3>
            <p>Advanced ML models predict shipment delays before they occur, enabling proactive intervention and customer communication.</p>
            <ul>
              <li>Carrier reliability analysis</li>
              <li>Route delay patterns</li>
              <li>Seasonal risk factors</li>
            </ul>
          </div>
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <CalendarClock size={32} />
            </div>
            <h3>Real-time Monitoring</h3>
            <p>Continuous tracking of shipments across all transport modes with automated risk scoring and status updates.</p>
            <ul>
              <li>AIR, SEA, LAND tracking</li>
              <li>Automatic risk recalculation</li>
              <li>Exception alerts</li>
            </ul>
          </div>
          <div className="erp-solution-card">
            <div className="erp-solution-icon">
              <Boxes size={32} />
            </div>
            <h3>Operations Optimization</h3>
            <p>Smart prioritization helps teams focus on high-risk shipments with actionable recommendations and AI explanations.</p>
            <ul>
              <li>Risk-based work queues</li>
              <li>AI-powered insights</li>
              <li>Performance analytics</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="erp-features" id="features">
        <div className="erp-section-header">
          <h2>Platform Capabilities</h2>
          <p>Enterprise-grade features for logistics operations teams</p>
        </div>
        <div className="erp-features-list">
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Intelligent Risk Scoring</h4>
              <p>Multi-factor analysis using carrier performance, route history, cargo type, and seasonal patterns</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>AI-Powered Explanations</h4>
              <p>Understand risk factors with natural language explanations powered by retrieval-augmented generation</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Comprehensive Analytics</h4>
              <p>Historical analysis, carrier performance metrics, and pattern identification for continuous improvement</p>
            </div>
          </div>
          <div className="erp-feature-item">
            <div className="erp-feature-check">✓</div>
            <div className="erp-feature-text">
              <h4>Enterprise Integration</h4>
              <p>Oracle database support, API-first architecture, and scalable deployment options</p>
            </div>
          </div>
        </div>
      </section>

      <section className="erp-cta">
        <div className="erp-cta-content">
          <h2>Ready to Transform Your Logistics Operations?</h2>
          <p>Join forward-thinking companies using ShipGuard to reduce delays and improve customer satisfaction.</p>
          <div className="erp-cta-buttons">
            <button className="erp-primary-btn large" onClick={onEnter}>
              Start Using ShipGuard
            </button>
            <button className="erp-secondary-btn large">
              Contact Sales
            </button>
          </div>
        </div>
      </section>

      <footer className="erp-footer">
        <div className="erp-footer-content">
          <div className="erp-footer-brand">
            <div className="erp-logo">
              <ShieldCheck size={24} />
              <span>ShipGuard</span>
            </div>
            <p>Intelligent Freight Forwarding Risk Management</p>
          </div>
          <div className="erp-footer-links">
            <div className="erp-footer-column">
              <h4>Product</h4>
              <a href="#solutions">Solutions</a>
              <a href="#features">Features</a>
              <a href="#">Pricing</a>
            </div>
            <div className="erp-footer-column">
              <h4>Company</h4>
              <a href="#">About</a>
              <a href="#">Careers</a>
              <a href="#">Contact</a>
            </div>
            <div className="erp-footer-column">
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">API Reference</a>
              <a href="#">Support</a>
            </div>
          </div>
        </div>
        <div className="erp-footer-bottom">
          <p>© 2026 ShipGuard. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
}
