const StatCard = ({ title, value, subtitle, icon, colorClass = 'stat-blue', trend }) => (
  <div className={`stat-card ${colorClass}`}>
    <div className="stat-card-body">
      <div className="stat-info">
        <p className="stat-label">{title}</p>
        <p className="stat-value">{value}</p>
        {subtitle && <p className="stat-sub">{subtitle}</p>}
        {trend !== undefined && (
          <p className={`stat-trend ${trend >= 0 ? 'trend-up' : 'trend-down'}`}>
            <i className={`bi bi-arrow-${trend >= 0 ? 'up' : 'down'}-right`}></i>
            {Math.abs(trend)}% vs yesterday
          </p>
        )}
      </div>
      {icon && (
        <div className="stat-icon-wrap">
          <i className={`bi bi-${icon}`}></i>
        </div>
      )}
    </div>
  </div>
);

export default StatCard;
