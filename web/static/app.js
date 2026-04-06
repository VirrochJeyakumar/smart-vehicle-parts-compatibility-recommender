const { useState, useEffect, useCallback } = React;

// API helpers
const api = {
  get: async (url) => {
    const r = await fetch(url);
    return r.json();
  },
};

// app
function App() {
  const [page, setPage] = useState("home");
  const [resultData, setResultData] = useState(null);
  const [searchParams, setSearchParams] = useState({});

  const showResults = (data, params) => {
    setResultData(data);
    setSearchParams(params);
    setPage("results");
    window.scrollTo(0, 0);
  };

  return (
    <div>
      <Header onLogoClick={() => setPage("home")} />
      <div className="container">
        {page === "home" && <HomePage onSearch={showResults} />}
        {page === "results" && (
          <ResultsPage
            data={resultData}
            params={searchParams}
            onBack={() => setPage("home")}
          />
        )}
      </div>
    </div>
  );
}

// header
function Header({ onLogoClick }) {
  return (
    <div className="header">
      <a
        href="#"
        className="logo"
        onClick={(e) => {
          e.preventDefault();
          onLogoClick();
        }}
      >
        <div className="logo-icon">VJ</div>
        <div>
          <div className="logo-text">Smart Parts Recommender</div>
          <div className="logo-sub">Vehicle Compatibility Engine</div>
        </div>
      </a>
      <span className="header-tag">CS310</span>
    </div>
  );
}

// home page
function HomePage({ onSearch }) {
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [years, setYears] = useState([]);
  const [stats, setStats] = useState(null);

  const [make, setMake] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [budget, setBudget] = useState("");
  const [vendors, setVendors] = useState("");
  const [bundleSize, setBundleSize] = useState("3");

  const [loading, setLoading] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  const [loadingYears, setLoadingYears] = useState(false);

  useEffect(() => {
    api.get("/api/makes").then(setMakes);
    api.get("/api/stats").then(setStats);
  }, []);

  const handleMakeChange = async (val) => {
    setMake(val);
    setModel("");
    setYear("");
    setModels([]);
    setYears([]);
    if (val) {
      setLoadingModels(true);
      const m = await api.get(`/api/models/${val}`);
      setModels(m);
      setLoadingModels(false);
    }
  };

  const handleModelChange = async (val) => {
    setModel(val);
    setYear("");
    setYears([]);
    if (val && make) {
      setLoadingYears(true);
      const y = await api.get(`/api/years/${make}/${val}`);
      setYears(y);
      setLoadingYears(false);
    }
  };

  const handleSearch = async () => {
    if (!make || !model || !year) return;
    setLoading(true);
    let url = `/api/recommend?make=${make}&model=${model}&year=${year}&bundle_size=${bundleSize || 3}`;
    if (budget) url += `&budget=${budget}`;
    if (vendors) url += `&vendors=${vendors}`;
    const data = await api.get(url);
    setLoading(false);
    onSearch(data, { make, model, year, budget, vendors, bundleSize });
  };

  const canSearch = make && model && year;

  return (
    <div>
      <div className="hero fade-up">
        <h1>
          Find <span className="grad">Compatible Parts</span>
          <br />& Smart Bundles
        </h1>
        <p>
          Select your vehicle to discover compatible parts, intelligently scored
          and bundled for the best value.
        </p>
      </div>

      {/* Vehicle Selection */}
      <div className="card fade-up" style={{ animationDelay: ".1s" }}>
        <div className="card-label">
          <span className="dot"></span> Vehicle Selection
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label>Make</label>
            <select
              value={make}
              onChange={(e) => handleMakeChange(e.target.value)}
            >
              <option value="">Select make...</option>
              {makes.map((m) => (
                <option key={m} value={m}>
                  {m.charAt(0).toUpperCase() + m.slice(1)}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Model</label>
            <select
              value={model}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={!make || loadingModels}
            >
              <option value="">
                {loadingModels
                  ? "Loading..."
                  : !make
                    ? "Select make first"
                    : "Select model..."}
              </option>
              {models.map((m) => (
                <option key={m} value={m}>
                  {m.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label>Year</label>
            <select
              value={year}
              onChange={(e) => setYear(e.target.value)}
              disabled={!model || loadingYears}
            >
              <option value="">
                {loadingYears
                  ? "Loading..."
                  : !model
                    ? "Select model first"
                    : "Select year..."}
              </option>
              {years.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="card fade-up" style={{ animationDelay: ".2s" }}>
        <div className="card-label">
          <span className="dot" style={{ background: "var(--gn)" }}></span>{" "}
          Bundle Preferences
        </div>
        <div className="form-grid">
          <div className="form-group">
            <label>Max Budget (£)</label>
            <input
              type="number"
              placeholder="No limit"
              min="0"
              step="0.01"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Max Vendors</label>
            <input
              type="number"
              placeholder="Maximum 20"
              min="0"
              max="20"
              value={vendors}
              onChange={(e) => setVendors(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label>Parts per Bundle</label>
            <input
              type="number"
              min="2"
              max="6"
              value={bundleSize}
              onChange={(e) => setBundleSize(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Search Button */}
      <div
        style={{
          textAlign: "center",
          margin: "1.5rem 0",
          animationDelay: ".3s",
        }}
        className="fade-up"
      >
        <button
          className="btn btn-primary"
          disabled={!canSearch || loading}
          onClick={handleSearch}
        >
          {loading ? (
            <span>
              Searching
              <span style={{ animation: "pulse 1s infinite" }}>...</span>
            </span>
          ) : (
            <span>&rarr; Find Compatible Parts &larr;</span>
          )}
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="card fade-up" style={{ animationDelay: ".35s" }}>
          <div className="card-label">
            <span className="dot" style={{ background: "var(--am)" }}></span>{" "}
            Graph Database
          </div>
          <div className="stats">
            <div className="stat-item">
              <div className="stat-val">{stats.parts.toLocaleString()}</div>
              <div className="stat-lbl">Parts</div>
            </div>
            <div className="stat-item">
              <div className="stat-val">{stats.vehicles.toLocaleString()}</div>
              <div className="stat-lbl">Vehicles</div>
            </div>
            <div className="stat-item">
              <div className="stat-val">{stats.sellers.toLocaleString()}</div>
              <div className="stat-lbl">Sellers</div>
            </div>
            <div className="stat-item">
              <div className="stat-val">
                {stats.fits_edges.toLocaleString()}
              </div>
              <div className="stat-lbl">Compatibility Links</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// results page
function ResultsPage({ data, params, onBack }) {
  const [showParts, setShowParts] = useState(false);

  if (!data) return null;

  const bundles = data.bundles || [];
  const parts = data.parts || [];
  const cats = data.categories_found || [];

  return (
    <div>
      <button className="back" onClick={onBack}>
        &larr; Back to search
      </button>

      {/* Vehicle Header */}
      <div className="card scale-in">
        <div className="results-header">
          <div>
            <div className="vehicle-name">
              {params.make.charAt(0).toUpperCase() + params.make.slice(1)}{" "}
              {params.model.toUpperCase()}{" "}
              <span className="year">{params.year}</span>
            </div>
            <div
              style={{
                color: "var(--t2)",
                marginTop: ".3rem",
                fontSize: ".9rem",
              }}
            >
              {data.total_compatible_parts} compatible parts across{" "}
              {cats.length} categories
            </div>
            <div className="results-meta">
              {cats.map((c) => (
                <span key={c} className="tag tag-blue">
                  {c}
                </span>
              ))}
            </div>
          </div>
          <div
            style={{
              display: "flex",
              gap: ".4rem",
              flexWrap: "wrap",
              justifyContent: "flex-end",
            }}
          >
            <span className="tag tag-green">{data.elapsed_ms} ms</span>
            {params.budget && (
              <span className="tag tag-amber">Budget: £{params.budget}</span>
            )}
            {params.vendors && (
              <span className="tag tag-amber">
                Max: {params.vendors} vendors
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Bundles */}
      {bundles.length > 0 ? (
        <div>
          <div className="section-title">
            Recommended Bundles ({bundles.length})
          </div>
          {bundles.slice(0, 10).map((b, i) => (
            <BundleCard key={i} bundle={b} rank={i + 1} />
          ))}
        </div>
      ) : (
        <div className="empty card">
          <div className="empty-icon">BOX?</div>
          <div className="empty-msg">No bundles match your constraints</div>
          <p
            style={{
              color: "var(--t3)",
              marginTop: ".5rem",
              fontSize: ".85rem",
            }}
          >
            Try increasing your budget or relaxing vendor limits.
          </p>
          <button
            className="btn btn-ghost"
            style={{ marginTop: "1rem" }}
            onClick={onBack}
          >
            &larr; Adjust search
          </button>
        </div>
      )}

      {/* All Parts Toggle */}
      {parts.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <button
            className={`parts-toggle ${showParts ? "open" : ""}`}
            onClick={() => setShowParts(!showParts)}
          >
            <span>
              {showParts ? "Hide" : "Show"} all {parts.length} scored parts
            </span>
            <span className="arrow"> V (?)</span>
          </button>
          {showParts && (
            <div className="card parts-list fade-in">
              {parts.slice(0, 60).map((p, i) => (
                <PartRow key={p.listing_id || i} part={p} rank={i + 1} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// bundle card
function BundleCard({ bundle, rank }) {
  const rankClass = rank === 1 ? "r1" : rank === 2 ? "r2" : "r3";
  const delay = `${rank * 0.06}s`;

  return (
    <div className="bundle fade-up" style={{ animationDelay: delay }}>
      <div className="bundle-top">
        <div className={`bundle-rank ${rankClass}`}>{rank}</div>
        <div className="bundle-info">
          <div className="bundle-tags">
            <span className="tag tag-green">Score: {bundle.bundle_score}</span>
            <span className="tag tag-amber">
              {bundle.num_sellers} vendor
              {bundle.num_sellers !== 1 ? "s" : ""}
            </span>
            {bundle.seller_names && bundle.seller_names.length > 0 && (
              <span className="tag tag-ghost">
                {bundle.seller_names.join(", ")}
              </span>
            )}
          </div>
        </div>
        <div className="bundle-price">£{bundle.total_price.toFixed(2)}</div>
      </div>
      <div className="bundle-parts">
        {bundle.parts.map((p, i) => (
          <div className="part-line" key={i}>
            <span className="part-cat">
              <span className="tag tag-blue">{p.category || "other"}</span>
            </span>
            <div className="part-detail">
              <div className="part-title">{p.title}</div>
              <div className="part-seller">
                {p.seller || "unknown"}
                {p.seller_rating ? ` • ${p.seller_rating}% rating` : ""}
              </div>
            </div>
            <span className="part-price-sm">
              {p.price ? `£${parseFloat(p.price).toFixed(2)}` : "N/A"}
            </span>
            {p.url && (
              <a
                href={p.url}
                target="_blank"
                rel="noopener"
                className="part-link"
              >
                eBay -{">"}
              </a>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// part row
function PartRow({ part, rank }) {
  const pct = Math.round((part.score || 0) * 100);
  const fillClass = pct >= 80 ? "high" : pct >= 50 ? "mid" : "low";

  return (
    <div className="part-row">
      <span className="part-row-rank">{rank}</span>
      <span className="part-cat">
        <span className="tag tag-blue">{part.category || "-"}</span>
      </span>
      <div className="part-detail" style={{ flex: 1, minWidth: 0 }}>
        <div className="part-title">{part.title}</div>
        <div className="part-seller">
          {part.seller || "unknown"}
          {part.seller_rating ? ` • ${part.seller_rating}%` : ""}
        </div>
      </div>
      <div className="score-bar">
        <div
          className={`score-fill ${fillClass}`}
          style={{ width: `${pct}%` }}
        ></div>
      </div>
      <span
        className="tag tag-green mono"
        style={{
          marginLeft: ".3rem",
          minWidth: "42px",
          justifyContent: "center",
        }}
      >
        {part.score}
      </span>
      <span className="part-price-sm">
        {part.price ? `£${parseFloat(part.price).toFixed(2)}` : `N/A`}
      </span>
      {part.url && (
        <a href={part.url} target="_blank" rel="noopener" className="part-link">
          eBay -{">"}
        </a>
      )}
    </div>
  );
}

// mount
ReactDOM.render(<App />, document.getElementById("root"));
