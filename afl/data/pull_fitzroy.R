# Pull what the fitzRoy mirror does not hold, one season at a time, into afl/cache/raw/*.csv.gz.
#
#   fryzigg_<season>   Fryzigg's per-player-per-game advanced stats (one API call per season)
#   odds_<season>      Footywire's betting odds per game (head-to-head and line)
#   squiggle_games_<season>, squiggle_tips_<season>   Squiggle results and every model's tips
#
# A file already on the afl-history release is downloaded into afl/cache/raw before this runs
# and is never pulled again (only seasons named in REFRESH are). Each call is followed by a
# pause so no site sees more than one request every few seconds. A season a source does not
# have is written down and skipped, not retried.
#
# Env: SEASONS ("2012:2026"), REFRESH (comma list of seasons to re-pull, e.g. the current one),
#      SQUIGGLE_UA (who we are, for Squiggle's admin), PAUSE (seconds between calls, default 5)

suppressPackageStartupMessages({
  library(fitzRoy)
  library(dplyr)
})

out <- "afl/cache/raw"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
seasons <- eval(parse(text = Sys.getenv("SEASONS", "2012:2026")))
refresh <- as.integer(strsplit(Sys.getenv("REFRESH", ""), ",")[[1]])
pause <- as.numeric(Sys.getenv("PAUSE", "5"))
ua <- Sys.getenv("SQUIGGLE_UA", "fk-model AFL research (private)")
log <- character()

held <- function(name, season) {
  f <- file.path(out, paste0(name, "_", season, ".csv.gz"))
  file.exists(f) && !(season %in% refresh)
}

save <- function(df, name, season) {
  f <- file.path(out, paste0(name, "_", season, ".csv.gz"))
  if (is.null(df) || nrow(df) == 0) {
    log <<- c(log, sprintf("%s %s: none", name, season))
    return(invisible(FALSE))
  }
  readr::write_csv(df, gzfile(f))
  log <<- c(log, sprintf("%s %s: %d rows", name, season, nrow(df)))
  invisible(TRUE)
}

attempt <- function(name, season, fn) {
  if (held(name, season)) {
    log <<- c(log, sprintf("%s %s: held, not pulled", name, season))
    return(invisible(NULL))
  }
  res <- tryCatch(fn(), error = function(e) {
    log <<- c(log, sprintf("%s %s: FAILED %s", name, season, conditionMessage(e)))
    NULL
  })
  if (!is.null(res)) save(res, name, season)
  Sys.sleep(pause)
}

for (s in seasons) {
  attempt("fryzigg", s, function() fetch_player_stats_fryzigg(season = s, comp = "AFLM"))
  attempt("odds", s, function() fetch_betting_odds_footywire(start_season = s, end_season = s))
  attempt("squiggle_games", s, function() fetch_squiggle_data(query = "games", year = s, user_agent = ua))
  attempt("squiggle_tips", s, function() fetch_squiggle_data(query = "tips", year = s, user_agent = ua))
}

writeLines(log)
writeLines(log, file.path(out, "pull_log.txt"))
