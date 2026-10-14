# Track x rail x run style, every race we hold (15 Oct 2026, research/form_gbm/t_rail_bias.py)

Won = winners; BSP expected / open expected = the sum of each price's chance; won/BSP 120% = won 20% more than BSP said. Cells with 30+ runners. Rails recovered from later past-run records (scripts/race_rails.py): 4,750 of 4,858 races.

races with a rail: 4750 of 4858  (by band: {np.str_('true'): 2688, np.str_('out 1-4m'): 891, np.str_('out 5-8m'): 806, np.str_('out 9m+'): 385, np.str_(''): 88})
runners with an actual settling position: 83%

### By how the horse ACTUALLY raced (the bias itself)
| track | rail | style | runners | races | won | BSP expected | won/BSP | open expected | won/open |
|---|---|---|---|---|---|---|---|---|---|
| ALL | true | lead | 2206 | 2205 | 457 | 316.8 | 144% | 296.6 | 154% |
| ALL | true | on pace | 5819 | 2578 | 765 | 718.6 | 106% | 671.8 | 114% |
| ALL | true | midfield | 6645 | 2595 | 696 | 669.2 | 104% | 663.8 | 105% |
| ALL | true | back | 7385 | 2611 | 466 | 556.2 | 84% | 597.6 | 78% |
| ALL | out 1-4m | lead | 769 | 769 | 158 | 101.7 | 155% | 97.1 | 163% |
| ALL | out 1-4m | on pace | 1977 | 855 | 265 | 236.8 | 112% | 230.1 | 115% |
| ALL | out 1-4m | midfield | 2226 | 868 | 246 | 236.9 | 104% | 230.0 | 107% |
| ALL | out 1-4m | back | 2499 | 872 | 150 | 195.3 | 77% | 206.7 | 73% |
| ALL | out 5-8m | lead | 696 | 696 | 139 | 99.1 | 140% | 91.5 | 152% |
| ALL | out 5-8m | on pace | 1757 | 799 | 265 | 223.8 | 118% | 212.8 | 125% |
| ALL | out 5-8m | midfield | 2016 | 807 | 196 | 218.5 | 90% | 217.5 | 90% |
| ALL | out 5-8m | back | 2217 | 806 | 144 | 176.2 | 82% | 186.7 | 77% |
| ALL | out 9m+ | lead | 340 | 340 | 57 | 46.7 | 122% | 44.3 | 129% |
| ALL | out 9m+ | on pace | 879 | 383 | 123 | 102.6 | 120% | 97.5 | 126% |
| ALL | out 9m+ | midfield | 999 | 390 | 105 | 104.0 | 101% | 103.5 | 101% |
| ALL | out 9m+ | back | 1100 | 391 | 79 | 88.4 | 89% | 94.6 | 84% |
| Geelong | true | lead | 68 | 67 | 12 | 10.6 | 113% | 8.9 | 134% |
| Geelong | true | on pace | 188 | 75 | 30 | 22.9 | 131% | 20.7 | 145% |
| Geelong | true | midfield | 211 | 76 | 21 | 20.8 | 101% | 21.2 | 99% |
| Geelong | true | back | 230 | 76 | 8 | 14.0 | 57% | 17.6 | 45% |
| Geelong | out 1-4m | lead | 33 | 33 | 8 | 4.7 | 171% | 4.3 | 184% |
| Geelong | out 1-4m | on pace | 82 | 35 | 8 | 8.7 | 92% | 9.2 | 87% |
| Geelong | out 1-4m | midfield | 94 | 37 | 10 | 11.6 | 86% | 11.0 | 91% |
| Geelong | out 1-4m | back | 105 | 37 | 8 | 8.1 | 99% | 8.2 | 98% |
| Geelong | out 5-8m | lead | 62 | 62 | 18 | 11.1 | 163% | 9.6 | 188% |
| Geelong | out 5-8m | on pace | 146 | 68 | 26 | 18.2 | 143% | 17.9 | 146% |
| Geelong | out 5-8m | midfield | 167 | 69 | 13 | 16.4 | 79% | 16.9 | 77% |
| Geelong | out 5-8m | back | 182 | 69 | 3 | 13.3 | 23% | 14.2 | 21% |
| Geelong | out 9m+ | lead | 53 | 53 | 11 | 5.8 | 190% | 5.9 | 186% |
| Geelong | out 9m+ | on pace | 138 | 62 | 17 | 17.2 | 99% | 15.9 | 107% |
| Geelong | out 9m+ | midfield | 161 | 62 | 23 | 17.6 | 131% | 17.6 | 131% |
| Geelong | out 9m+ | back | 169 | 61 | 11 | 13.5 | 82% | 14.7 | 75% |
| Caulfield | true | lead | 66 | 66 | 9 | 7.8 | 115% | 6.9 | 131% |
| Caulfield | true | on pace | 180 | 75 | 23 | 21.2 | 108% | 19.6 | 117% |
| Caulfield | true | midfield | 212 | 77 | 22 | 19.8 | 111% | 21.1 | 104% |
| Caulfield | true | back | 235 | 77 | 18 | 20.4 | 88% | 21.5 | 84% |
| Caulfield | out 1-4m | lead | 53 | 53 | 9 | 6.6 | 136% | 5.8 | 154% |
| Caulfield | out 1-4m | on pace | 151 | 58 | 21 | 17.6 | 119% | 16.1 | 131% |
| Caulfield | out 1-4m | midfield | 163 | 56 | 16 | 14.0 | 114% | 14.1 | 113% |
| Caulfield | out 1-4m | back | 192 | 58 | 10 | 13.0 | 77% | 14.7 | 68% |
| Caulfield | out 5-8m | lead | 42 | 42 | 6 | 5.0 | 119% | 4.4 | 135% |
| Caulfield | out 5-8m | on pace | 118 | 47 | 20 | 14.6 | 137% | 13.1 | 152% |
| Caulfield | out 5-8m | midfield | 125 | 48 | 8 | 12.3 | 65% | 12.2 | 66% |
| Caulfield | out 5-8m | back | 145 | 48 | 10 | 10.8 | 93% | 12.1 | 83% |
| Caulfield | out 9m+ | lead | 50 | 50 | 12 | 7.9 | 151% | 7.2 | 166% |
| Caulfield | out 9m+ | on pace | 137 | 56 | 17 | 14.7 | 115% | 13.7 | 124% |
| Caulfield | out 9m+ | midfield | 148 | 58 | 19 | 15.3 | 124% | 15.4 | 123% |
| Caulfield | out 9m+ | back | 165 | 58 | 7 | 12.4 | 56% | 13.8 | 51% |
| Ballarat Synthetic | true | lead | 174 | 174 | 36 | 33.2 | 109% | 29.0 | 124% |
| Ballarat Synthetic | true | on pace | 405 | 214 | 55 | 52.4 | 105% | 47.2 | 117% |
| Ballarat Synthetic | true | midfield | 483 | 217 | 63 | 52.0 | 121% | 51.4 | 123% |
| Ballarat Synthetic | true | back | 547 | 221 | 38 | 44.5 | 85% | 50.5 | 75% |
| Cranbourne | true | lead | 73 | 73 | 17 | 11.9 | 143% | 11.6 | 147% |
| Cranbourne | true | on pace | 141 | 77 | 20 | 20.3 | 98% | 19.1 | 105% |
| Cranbourne | true | midfield | 171 | 77 | 21 | 22.8 | 92% | 21.4 | 98% |
| Cranbourne | true | back | 187 | 79 | 15 | 14.8 | 101% | 16.4 | 92% |
| Cranbourne | out 1-4m | lead | 48 | 48 | 12 | 7.4 | 162% | 6.9 | 174% |
| Cranbourne | out 1-4m | on pace | 118 | 52 | 12 | 15.3 | 79% | 14.9 | 81% |
| Cranbourne | out 1-4m | midfield | 131 | 54 | 15 | 12.7 | 118% | 13.1 | 115% |
| Cranbourne | out 1-4m | back | 142 | 53 | 12 | 13.5 | 89% | 13.7 | 87% |
| Cranbourne | out 5-8m | lead | 53 | 53 | 14 | 8.7 | 160% | 7.8 | 179% |
| Cranbourne | out 5-8m | on pace | 115 | 56 | 17 | 15.7 | 108% | 14.4 | 118% |
| Cranbourne | out 5-8m | midfield | 132 | 55 | 17 | 18.9 | 90% | 18.2 | 93% |
| Cranbourne | out 5-8m | back | 143 | 53 | 7 | 9.2 | 76% | 11.8 | 59% |
| Cranbourne | out 9m+ | on pace | 54 | 29 | 10 | 8.1 | 123% | 7.8 | 128% |
| Cranbourne | out 9m+ | midfield | 61 | 29 | 7 | 7.3 | 95% | 7.2 | 97% |
| Cranbourne | out 9m+ | back | 68 | 30 | 4 | 5.8 | 69% | 6.1 | 66% |
| Flemington | true | lead | 60 | 60 | 8 | 8.7 | 92% | 7.6 | 106% |
| Flemington | true | on pace | 160 | 64 | 16 | 17.5 | 91% | 16.3 | 98% |
| Flemington | true | midfield | 176 | 65 | 20 | 15.3 | 131% | 15.9 | 126% |
| Flemington | true | back | 200 | 65 | 16 | 14.9 | 107% | 15.9 | 101% |
| Flemington | out 1-4m | lead | 46 | 46 | 7 | 4.2 | 168% | 4.3 | 162% |
| Flemington | out 1-4m | on pace | 140 | 53 | 16 | 14.6 | 109% | 14.0 | 115% |
| Flemington | out 1-4m | midfield | 152 | 54 | 16 | 14.5 | 110% | 13.8 | 116% |
| Flemington | out 1-4m | back | 170 | 52 | 13 | 10.5 | 123% | 11.5 | 113% |
| Flemington | out 5-8m | on pace | 89 | 37 | 9 | 8.7 | 103% | 9.3 | 97% |
| Flemington | out 5-8m | midfield | 104 | 37 | 9 | 10.9 | 82% | 10.2 | 89% |
| Flemington | out 5-8m | back | 115 | 37 | 7 | 8.5 | 82% | 8.5 | 82% |
| Flemington | out 9m+ | lead | 55 | 55 | 5 | 6.8 | 73% | 6.3 | 80% |
| Flemington | out 9m+ | on pace | 162 | 63 | 25 | 16.4 | 153% | 15.4 | 162% |
| Flemington | out 9m+ | midfield | 197 | 64 | 14 | 17.3 | 81% | 17.1 | 82% |
| Flemington | out 9m+ | back | 202 | 64 | 14 | 15.9 | 88% | 17.3 | 81% |
| Pakenham Park | true | lead | 35 | 35 | 5 | 6.1 | 81% | 6.5 | 77% |
| Pakenham Park | true | on pace | 89 | 47 | 11 | 11.3 | 98% | 10.6 | 104% |
| Pakenham Park | true | midfield | 107 | 46 | 17 | 12.6 | 135% | 11.8 | 144% |
| Pakenham Park | true | back | 119 | 47 | 11 | 10.9 | 101% | 10.8 | 102% |
| Pakenham Park | out 1-4m | lead | 58 | 58 | 6 | 4.9 | 123% | 5.6 | 107% |
| Pakenham Park | out 1-4m | on pace | 138 | 64 | 24 | 16.0 | 150% | 15.9 | 151% |
| Pakenham Park | out 1-4m | midfield | 158 | 64 | 18 | 20.8 | 87% | 19.5 | 93% |
| Pakenham Park | out 1-4m | back | 181 | 64 | 12 | 15.4 | 78% | 15.9 | 75% |
| Pakenham Park | out 5-8m | lead | 64 | 64 | 15 | 8.6 | 175% | 9.3 | 161% |
| Pakenham Park | out 5-8m | on pace | 158 | 71 | 22 | 22.7 | 97% | 21.4 | 103% |
| Pakenham Park | out 5-8m | midfield | 172 | 72 | 19 | 18.6 | 102% | 18.0 | 106% |
| Pakenham Park | out 5-8m | back | 187 | 71 | 15 | 16.1 | 93% | 17.1 | 88% |
| Pakenham Park | out 9m+ | on pace | 63 | 30 | 11 | 8.9 | 123% | 8.0 | 138% |
| Pakenham Park | out 9m+ | midfield | 78 | 31 | 11 | 8.7 | 127% | 9.0 | 122% |
| Pakenham Park | out 9m+ | back | 87 | 31 | 4 | 8.2 | 49% | 8.4 | 47% |
| Sandown Hillside | true | lead | 37 | 37 | 9 | 5.8 | 156% | 5.4 | 167% |
| Sandown Hillside | true | on pace | 87 | 38 | 13 | 10.8 | 121% | 10.1 | 129% |
| Sandown Hillside | true | midfield | 101 | 38 | 7 | 9.9 | 71% | 9.9 | 70% |
| Sandown Hillside | true | back | 113 | 37 | 7 | 9.1 | 77% | 9.9 | 70% |
| Sandown Hillside | out 1-4m | midfield | 34 | 15 | 5 | 5.0 | 99% | 4.8 | 105% |
| Sandown Hillside | out 1-4m | back | 44 | 16 | 1 | 4.0 | 25% | 4.2 | 24% |
| Sandown Hillside | out 5-8m | lead | 67 | 67 | 8 | 9.0 | 89% | 8.4 | 95% |
| Sandown Hillside | out 5-8m | on pace | 172 | 75 | 26 | 20.6 | 126% | 19.4 | 134% |
| Sandown Hillside | out 5-8m | midfield | 187 | 75 | 20 | 22.1 | 90% | 22.6 | 89% |
| Sandown Hillside | out 5-8m | back | 211 | 75 | 15 | 17.7 | 85% | 18.0 | 83% |
| Sandown Hillside | out 9m+ | lead | 58 | 58 | 6 | 7.5 | 80% | 6.6 | 92% |
| Sandown Hillside | out 9m+ | on pace | 153 | 63 | 18 | 17.4 | 103% | 17.1 | 105% |
| Sandown Hillside | out 9m+ | midfield | 152 | 63 | 11 | 16.0 | 69% | 16.0 | 69% |
| Sandown Hillside | out 9m+ | back | 173 | 63 | 24 | 15.7 | 153% | 16.3 | 147% |
| Warrnambool | true | lead | 70 | 70 | 14 | 10.3 | 135% | 10.8 | 130% |
| Warrnambool | true | on pace | 191 | 82 | 28 | 20.3 | 138% | 20.1 | 139% |
| Warrnambool | true | midfield | 222 | 81 | 17 | 22.2 | 77% | 20.9 | 81% |
| Warrnambool | true | back | 246 | 81 | 17 | 18.9 | 90% | 19.0 | 89% |
| Warrnambool | out 1-4m | lead | 47 | 47 | 9 | 7.4 | 122% | 6.6 | 137% |
| Warrnambool | out 1-4m | on pace | 121 | 55 | 14 | 14.3 | 98% | 14.4 | 97% |
| Warrnambool | out 1-4m | midfield | 147 | 54 | 21 | 16.8 | 125% | 15.7 | 134% |
| Warrnambool | out 1-4m | back | 159 | 55 | 8 | 11.8 | 68% | 12.9 | 62% |
| Warrnambool | out 5-8m | lead | 32 | 32 | 3 | 4.5 | 66% | 4.9 | 62% |
| Warrnambool | out 5-8m | on pace | 81 | 37 | 12 | 10.1 | 119% | 9.3 | 129% |
| Warrnambool | out 5-8m | midfield | 91 | 38 | 11 | 9.8 | 112% | 10.1 | 108% |
| Warrnambool | out 5-8m | back | 94 | 38 | 8 | 9.4 | 85% | 8.7 | 92% |
| Bendigo | true | lead | 54 | 54 | 7 | 6.6 | 106% | 5.9 | 118% |
| Bendigo | true | on pace | 171 | 67 | 22 | 20.6 | 107% | 18.7 | 118% |
| Bendigo | true | midfield | 174 | 66 | 19 | 17.2 | 111% | 17.2 | 110% |
| Bendigo | true | back | 189 | 66 | 15 | 13.3 | 113% | 15.0 | 100% |
| Bendigo | out 1-4m | lead | 30 | 30 | 6 | 3.1 | 193% | 3.4 | 178% |
| Bendigo | out 1-4m | on pace | 76 | 31 | 13 | 9.4 | 139% | 8.6 | 151% |
| Bendigo | out 1-4m | midfield | 87 | 33 | 8 | 9.4 | 85% | 9.1 | 88% |
| Bendigo | out 1-4m | back | 102 | 33 | 4 | 8.0 | 50% | 8.6 | 47% |
| Bendigo | out 5-8m | on pace | 87 | 36 | 17 | 10.6 | 161% | 10.4 | 164% |
| Bendigo | out 5-8m | midfield | 92 | 36 | 9 | 9.0 | 100% | 8.7 | 103% |
| Bendigo | out 5-8m | back | 105 | 35 | 6 | 8.5 | 70% | 9.0 | 66% |
| Bendigo | out 9m+ | on pace | 65 | 30 | 12 | 8.0 | 150% | 7.1 | 168% |
| Bendigo | out 9m+ | midfield | 84 | 31 | 9 | 8.1 | 111% | 8.1 | 111% |
| Bendigo | out 9m+ | back | 85 | 32 | 4 | 6.5 | 62% | 7.0 | 57% |
| Sale | true | lead | 74 | 74 | 18 | 12.8 | 141% | 11.9 | 151% |
| Sale | true | on pace | 179 | 82 | 26 | 25.0 | 104% | 23.9 | 109% |
| Sale | true | midfield | 194 | 80 | 18 | 17.7 | 102% | 19.3 | 93% |
| Sale | true | back | 219 | 82 | 15 | 18.2 | 82% | 17.9 | 84% |
| Sale | out 1-4m | lead | 35 | 35 | 9 | 6.9 | 131% | 5.8 | 155% |
| Sale | out 1-4m | on pace | 77 | 36 | 12 | 9.5 | 127% | 9.7 | 124% |
| Sale | out 1-4m | midfield | 90 | 37 | 9 | 9.6 | 93% | 9.3 | 97% |
| Sale | out 1-4m | back | 96 | 36 | 7 | 6.5 | 107% | 7.5 | 93% |
| Sale | out 5-8m | lead | 38 | 38 | 10 | 5.2 | 191% | 4.5 | 223% |
| Sale | out 5-8m | on pace | 101 | 46 | 11 | 13.4 | 82% | 12.6 | 87% |
| Sale | out 5-8m | midfield | 112 | 47 | 12 | 11.3 | 106% | 11.5 | 105% |
| Sale | out 5-8m | back | 135 | 48 | 8 | 9.7 | 83% | 10.0 | 80% |
| Mornington | true | lead | 45 | 45 | 8 | 6.7 | 119% | 6.2 | 130% |
| Mornington | true | on pace | 122 | 57 | 14 | 15.8 | 89% | 14.9 | 94% |
| Mornington | true | midfield | 137 | 57 | 22 | 13.9 | 158% | 13.9 | 158% |
| Mornington | true | back | 166 | 58 | 7 | 13.0 | 54% | 14.6 | 48% |
| Mornington | out 1-4m | on pace | 44 | 23 | 11 | 6.9 | 161% | 6.4 | 171% |
| Mornington | out 1-4m | midfield | 46 | 23 | 6 | 4.8 | 124% | 5.3 | 114% |
| Mornington | out 1-4m | back | 50 | 23 | 0 | 5.0 | 0% | 5.3 | 0% |
| Mornington | out 5-8m | lead | 66 | 66 | 15 | 10.1 | 148% | 8.7 | 173% |
| Mornington | out 5-8m | on pace | 162 | 77 | 27 | 20.4 | 133% | 20.2 | 134% |
| Mornington | out 5-8m | midfield | 204 | 78 | 15 | 20.4 | 74% | 20.9 | 72% |
| Mornington | out 5-8m | back | 219 | 79 | 15 | 17.4 | 86% | 18.2 | 82% |
| Seymour | true | lead | 56 | 56 | 2 | 6.1 | 33% | 6.6 | 30% |
| Seymour | true | on pace | 186 | 69 | 25 | 20.1 | 124% | 18.9 | 132% |
| Seymour | true | midfield | 204 | 69 | 23 | 18.1 | 127% | 17.7 | 130% |
| Seymour | true | back | 222 | 69 | 15 | 15.7 | 95% | 15.6 | 96% |
| Seymour | out 1-4m | on pace | 78 | 30 | 11 | 9.5 | 116% | 8.2 | 134% |
| Seymour | out 1-4m | midfield | 83 | 31 | 9 | 7.5 | 119% | 7.9 | 114% |
| Seymour | out 1-4m | back | 98 | 31 | 4 | 7.6 | 52% | 7.8 | 51% |
| Seymour | out 5-8m | lead | 51 | 51 | 6 | 7.2 | 83% | 6.5 | 93% |
| Seymour | out 5-8m | on pace | 119 | 55 | 21 | 16.0 | 131% | 14.8 | 142% |
| Seymour | out 5-8m | midfield | 135 | 56 | 15 | 13.2 | 113% | 13.4 | 112% |
| Seymour | out 5-8m | back | 149 | 55 | 11 | 12.0 | 92% | 12.7 | 87% |
| Ballarat | true | lead | 55 | 55 | 10 | 7.9 | 126% | 7.5 | 133% |
| Ballarat | true | on pace | 141 | 60 | 17 | 16.1 | 105% | 15.1 | 112% |
| Ballarat | true | midfield | 160 | 60 | 18 | 15.6 | 115% | 14.6 | 124% |
| Ballarat | true | back | 176 | 60 | 13 | 13.2 | 99% | 14.6 | 89% |
| Ballarat | out 1-4m | on pace | 40 | 16 | 6 | 4.5 | 133% | 4.3 | 139% |
| Ballarat | out 1-4m | midfield | 47 | 18 | 7 | 4.9 | 144% | 4.4 | 161% |
| Ballarat | out 1-4m | back | 53 | 18 | 2 | 4.2 | 48% | 4.1 | 48% |
| Ballarat | out 5-8m | on pace | 64 | 30 | 10 | 7.3 | 138% | 7.5 | 134% |
| Ballarat | out 5-8m | midfield | 77 | 32 | 6 | 9.4 | 64% | 9.5 | 63% |
| Ballarat | out 5-8m | back | 81 | 32 | 9 | 8.0 | 112% | 7.5 | 120% |
| Ballarat | out 9m+ | on pace | 67 | 31 | 7 | 7.2 | 98% | 7.7 | 91% |
| Ballarat | out 9m+ | midfield | 67 | 32 | 8 | 9.1 | 88% | 8.4 | 95% |
| Ballarat | out 9m+ | back | 96 | 32 | 6 | 6.6 | 91% | 7.1 | 84% |
| Moe | true | lead | 60 | 60 | 15 | 7.7 | 196% | 7.1 | 211% |
| Moe | true | on pace | 172 | 73 | 21 | 20.1 | 104% | 19.4 | 108% |
| Moe | true | midfield | 200 | 76 | 27 | 20.6 | 131% | 19.8 | 137% |
| Moe | true | back | 227 | 77 | 9 | 16.1 | 56% | 17.0 | 53% |
| Moe | out 1-4m | lead | 30 | 30 | 8 | 4.2 | 192% | 4.1 | 193% |
| Moe | out 1-4m | on pace | 83 | 32 | 6 | 9.1 | 66% | 9.3 | 65% |
| Moe | out 1-4m | midfield | 84 | 32 | 8 | 8.4 | 95% | 7.8 | 102% |
| Moe | out 1-4m | back | 92 | 32 | 8 | 7.2 | 110% | 8.0 | 100% |
| Moe | out 5-8m | on pace | 60 | 29 | 9 | 8.7 | 103% | 8.3 | 108% |
| Moe | out 5-8m | midfield | 66 | 28 | 5 | 6.6 | 76% | 6.5 | 77% |
| Moe | out 5-8m | back | 76 | 29 | 4 | 4.9 | 82% | 4.9 | 82% |
| Pakenham Synthetic | true | lead | 105 | 105 | 18 | 12.9 | 139% | 12.1 | 149% |
| Pakenham Synthetic | true | on pace | 262 | 125 | 41 | 31.5 | 130% | 30.1 | 136% |
| Pakenham Synthetic | true | midfield | 329 | 124 | 30 | 33.2 | 90% | 32.0 | 94% |
| Pakenham Synthetic | true | back | 367 | 128 | 24 | 26.1 | 92% | 28.6 | 84% |
| Sandown Lakeside | true | lead | 42 | 42 | 8 | 5.1 | 156% | 4.6 | 173% |
| Sandown Lakeside | true | on pace | 120 | 50 | 12 | 15.5 | 77% | 13.7 | 87% |
| Sandown Lakeside | true | midfield | 135 | 50 | 18 | 12.7 | 141% | 13.3 | 135% |
| Sandown Lakeside | true | back | 147 | 50 | 10 | 11.1 | 90% | 11.9 | 84% |
| Sandown Lakeside | out 1-4m | lead | 35 | 35 | 10 | 4.6 | 218% | 4.5 | 222% |
| Sandown Lakeside | out 1-4m | on pace | 86 | 39 | 14 | 10.2 | 138% | 9.7 | 144% |
| Sandown Lakeside | out 1-4m | midfield | 100 | 40 | 11 | 10.0 | 110% | 10.3 | 107% |
| Sandown Lakeside | out 1-4m | back | 109 | 40 | 3 | 9.2 | 33% | 9.6 | 31% |
| Sandown Lakeside | out 5-8m | lead | 31 | 31 | 5 | 3.9 | 130% | 3.3 | 152% |
| Sandown Lakeside | out 5-8m | on pace | 70 | 32 | 10 | 8.5 | 117% | 7.6 | 132% |
| Sandown Lakeside | out 5-8m | midfield | 93 | 31 | 9 | 10.0 | 90% | 9.9 | 91% |
| Sandown Lakeside | out 5-8m | back | 93 | 32 | 7 | 7.8 | 89% | 8.9 | 79% |
| Echuca | true | lead | 91 | 91 | 18 | 10.9 | 166% | 11.0 | 163% |
| Echuca | true | on pace | 277 | 117 | 27 | 33.8 | 80% | 30.1 | 90% |
| Echuca | true | midfield | 319 | 117 | 27 | 30.7 | 88% | 30.5 | 88% |
| Echuca | true | back | 331 | 115 | 35 | 26.8 | 131% | 29.0 | 121% |
| Wangaratta | true | lead | 46 | 46 | 8 | 4.2 | 191% | 3.9 | 203% |
| Wangaratta | true | on pace | 158 | 58 | 24 | 16.9 | 142% | 16.8 | 143% |
| Wangaratta | true | midfield | 173 | 58 | 9 | 13.2 | 68% | 13.1 | 69% |
| Wangaratta | true | back | 183 | 58 | 10 | 13.1 | 76% | 12.9 | 78% |
| Wangaratta | out 1-4m | lead | 51 | 51 | 14 | 6.3 | 223% | 5.6 | 249% |
| Wangaratta | out 1-4m | on pace | 147 | 58 | 16 | 19.2 | 84% | 18.5 | 86% |
| Wangaratta | out 1-4m | midfield | 148 | 57 | 14 | 14.3 | 98% | 13.8 | 101% |
| Wangaratta | out 1-4m | back | 175 | 58 | 10 | 12.3 | 81% | 13.1 | 76% |
| Kilmore | true | lead | 54 | 54 | 14 | 7.1 | 197% | 7.2 | 193% |
| Kilmore | true | on pace | 132 | 59 | 14 | 17.9 | 78% | 17.2 | 81% |
| Kilmore | true | midfield | 152 | 58 | 16 | 14.7 | 109% | 14.1 | 113% |
| Kilmore | true | back | 159 | 58 | 10 | 11.1 | 90% | 11.2 | 89% |
| Kilmore | out 1-4m | on pace | 66 | 28 | 8 | 7.8 | 103% | 7.8 | 103% |
| Kilmore | out 1-4m | midfield | 85 | 31 | 9 | 9.0 | 100% | 8.5 | 106% |
| Kilmore | out 1-4m | back | 92 | 31 | 5 | 6.5 | 77% | 6.9 | 73% |
| Kilmore | out 5-8m | on pace | 35 | 15 | 4 | 4.4 | 91% | 4.4 | 91% |
| Kilmore | out 5-8m | midfield | 39 | 16 | 5 | 4.2 | 119% | 4.0 | 125% |
| Kilmore | out 5-8m | back | 42 | 16 | 2 | 3.8 | 52% | 3.7 | 54% |
| Caulfield Heath | true | lead | 39 | 39 | 8 | 5.4 | 148% | 5.4 | 148% |
| Caulfield Heath | true | on pace | 76 | 38 | 11 | 10.6 | 104% | 9.7 | 113% |
| Caulfield Heath | true | midfield | 91 | 41 | 12 | 11.2 | 107% | 10.8 | 111% |
| Caulfield Heath | true | back | 105 | 41 | 7 | 10.1 | 69% | 10.7 | 65% |
| Caulfield Heath | out 1-4m | lead | 41 | 41 | 7 | 5.9 | 120% | 5.6 | 124% |
| Caulfield Heath | out 1-4m | on pace | 89 | 45 | 12 | 11.6 | 103% | 11.6 | 103% |
| Caulfield Heath | out 1-4m | midfield | 110 | 48 | 13 | 14.1 | 92% | 13.2 | 98% |
| Caulfield Heath | out 1-4m | back | 125 | 49 | 9 | 10.1 | 89% | 11.5 | 78% |
| Caulfield Heath | out 5-8m | midfield | 34 | 16 | 2 | 4.1 | 48% | 4.0 | 50% |
| Caulfield Heath | out 5-8m | back | 41 | 16 | 4 | 3.4 | 118% | 3.5 | 115% |
| Swan Hill | true | lead | 80 | 80 | 13 | 9.0 | 144% | 8.3 | 156% |
| Swan Hill | true | on pace | 238 | 96 | 27 | 24.0 | 113% | 23.9 | 113% |
| Swan Hill | true | midfield | 259 | 99 | 25 | 26.7 | 94% | 25.7 | 97% |
| Swan Hill | true | back | 291 | 97 | 19 | 23.7 | 80% | 23.7 | 80% |
| Wodonga | true | lead | 44 | 44 | 11 | 5.6 | 198% | 5.6 | 195% |
| Wodonga | true | on pace | 139 | 65 | 19 | 18.0 | 105% | 16.3 | 117% |
| Wodonga | true | midfield | 162 | 67 | 20 | 16.7 | 120% | 16.8 | 119% |
| Wodonga | true | back | 187 | 68 | 7 | 14.3 | 49% | 14.7 | 48% |
| Wodonga | out 1-4m | on pace | 55 | 29 | 10 | 8.1 | 123% | 7.6 | 132% |
| Wodonga | out 1-4m | midfield | 68 | 30 | 8 | 8.2 | 97% | 7.6 | 106% |
| Wodonga | out 1-4m | back | 77 | 30 | 6 | 6.8 | 88% | 7.5 | 80% |
| Kyneton | out 1-4m | lead | 44 | 44 | 9 | 5.5 | 163% | 5.7 | 159% |
| Kyneton | out 1-4m | on pace | 112 | 50 | 15 | 14.0 | 107% | 13.0 | 115% |
| Kyneton | out 1-4m | midfield | 135 | 49 | 16 | 15.2 | 105% | 14.5 | 111% |
| Kyneton | out 1-4m | back | 142 | 50 | 8 | 10.6 | 75% | 11.3 | 71% |
| Kyneton | out 5-8m | on pace | 68 | 33 | 10 | 9.1 | 110% | 8.8 | 114% |
| Kyneton | out 5-8m | midfield | 83 | 33 | 9 | 9.6 | 94% | 9.0 | 100% |
| Kyneton | out 5-8m | back | 94 | 33 | 5 | 6.4 | 78% | 7.8 | 64% |
| Bairnsdale | true | lead | 48 | 48 | 7 | 4.9 | 142% | 4.7 | 148% |
| Bairnsdale | true | on pace | 145 | 57 | 21 | 17.8 | 118% | 16.4 | 128% |
| Bairnsdale | true | midfield | 165 | 57 | 10 | 14.0 | 71% | 13.9 | 72% |
| Bairnsdale | true | back | 189 | 58 | 13 | 11.7 | 111% | 13.0 | 100% |
| Bairnsdale | out 1-4m | midfield | 31 | 14 | 2 | 2.3 | 85% | 2.7 | 73% |
| Bairnsdale | out 1-4m | back | 30 | 14 | 3 | 3.0 | 100% | 2.7 | 111% |
| Mildura | true | lead | 55 | 55 | 14 | 7.5 | 188% | 6.6 | 212% |
| Mildura | true | on pace | 129 | 68 | 15 | 14.2 | 106% | 13.6 | 110% |
| Mildura | true | midfield | 153 | 67 | 11 | 15.3 | 72% | 14.7 | 75% |
| Mildura | true | back | 171 | 69 | 14 | 12.9 | 108% | 13.9 | 101% |
| Hamilton | true | lead | 63 | 63 | 22 | 11.3 | 195% | 11.2 | 196% |
| Hamilton | true | on pace | 145 | 64 | 23 | 20.4 | 113% | 18.5 | 124% |
| Hamilton | true | midfield | 149 | 67 | 15 | 17.3 | 87% | 17.8 | 84% |
| Hamilton | true | back | 165 | 66 | 5 | 12.4 | 40% | 13.1 | 38% |
| Werribee | true | on pace | 50 | 22 | 5 | 5.7 | 87% | 5.3 | 93% |
| Werribee | true | midfield | 60 | 22 | 10 | 6.8 | 147% | 6.9 | 145% |
| Werribee | true | back | 62 | 22 | 3 | 4.2 | 71% | 4.4 | 67% |
| Werribee | out 1-4m | on pace | 36 | 15 | 4 | 3.6 | 111% | 3.9 | 102% |
| Werribee | out 1-4m | midfield | 37 | 15 | 3 | 3.9 | 77% | 3.6 | 83% |
| Werribee | out 1-4m | back | 43 | 14 | 2 | 3.1 | 64% | 3.1 | 65% |
| Werribee | out 5-8m | on pace | 56 | 23 | 6 | 6.4 | 94% | 6.0 | 100% |
| Werribee | out 5-8m | midfield | 58 | 23 | 7 | 6.8 | 102% | 6.3 | 111% |
| Werribee | out 5-8m | back | 63 | 23 | 6 | 5.5 | 110% | 5.6 | 107% |
| Moonee Valley | true | lead | 35 | 35 | 9 | 4.7 | 190% | 4.2 | 214% |
| Moonee Valley | true | on pace | 78 | 35 | 8 | 9.3 | 86% | 9.3 | 86% |
| Moonee Valley | true | midfield | 89 | 37 | 10 | 8.6 | 116% | 8.8 | 114% |
| Moonee Valley | true | back | 108 | 37 | 10 | 10.7 | 93% | 10.9 | 92% |
| Moonee Valley | out 5-8m | on pace | 32 | 17 | 5 | 5.3 | 94% | 4.4 | 114% |
| Moonee Valley | out 5-8m | midfield | 45 | 17 | 5 | 4.7 | 106% | 5.5 | 91% |
| Moonee Valley | out 5-8m | back | 42 | 17 | 2 | 3.9 | 51% | 4.5 | 45% |
| Yarra Valley | true | on pace | 68 | 30 | 10 | 8.7 | 115% | 8.9 | 112% |
| Yarra Valley | true | midfield | 80 | 31 | 12 | 9.7 | 124% | 8.4 | 142% |
| Yarra Valley | true | back | 96 | 31 | 5 | 7.2 | 70% | 7.3 | 69% |
| Yarra Valley | out 1-4m | on pace | 76 | 31 | 14 | 9.8 | 143% | 9.3 | 150% |
| Yarra Valley | out 1-4m | midfield | 79 | 31 | 4 | 8.0 | 50% | 8.1 | 50% |
| Yarra Valley | out 1-4m | back | 82 | 31 | 6 | 7.3 | 83% | 7.2 | 83% |
| Donald | true | lead | 42 | 42 | 7 | 5.5 | 126% | 4.8 | 145% |
| Donald | true | on pace | 124 | 53 | 20 | 16.3 | 123% | 14.2 | 140% |
| Donald | true | midfield | 139 | 52 | 12 | 14.1 | 85% | 14.5 | 83% |
| Donald | true | back | 172 | 53 | 8 | 10.4 | 77% | 12.1 | 66% |

### By Form King's PREDICTED settling position (known before the race)
| track | rail | style | runners | races | won | BSP expected | won/BSP | open expected | won/open |
|---|---|---|---|---|---|---|---|---|---|
| ALL | true | lead | 2614 | 2614 | 343 | 359.3 | 95% | 337.6 | 102% |
| ALL | true | on pace | 6940 | 2624 | 760 | 753.6 | 101% | 744.3 | 102% |
| ALL | true | midfield | 7865 | 2626 | 738 | 753.1 | 98% | 777.0 | 95% |
| ALL | true | back | 8939 | 2627 | 786 | 761.0 | 103% | 768.1 | 102% |
| ALL | out 1-4m | lead | 880 | 880 | 124 | 120.4 | 103% | 115.2 | 108% |
| ALL | out 1-4m | on pace | 2326 | 880 | 245 | 250.7 | 98% | 251.2 | 98% |
| ALL | out 1-4m | midfield | 2625 | 883 | 271 | 255.9 | 106% | 259.5 | 104% |
| ALL | out 1-4m | back | 2928 | 883 | 243 | 256.0 | 95% | 257.1 | 95% |
| ALL | out 5-8m | lead | 816 | 816 | 122 | 114.0 | 107% | 108.4 | 113% |
| ALL | out 5-8m | on pace | 2019 | 816 | 224 | 219.7 | 102% | 223.1 | 100% |
| ALL | out 5-8m | midfield | 2326 | 816 | 236 | 233.9 | 101% | 238.5 | 99% |
| ALL | out 5-8m | back | 2603 | 817 | 235 | 249.4 | 94% | 247.0 | 95% |
| ALL | out 9m+ | lead | 395 | 395 | 53 | 54.8 | 97% | 51.1 | 104% |
| ALL | out 9m+ | on pace | 1038 | 396 | 93 | 109.8 | 85% | 112.8 | 82% |
| ALL | out 9m+ | midfield | 1167 | 396 | 125 | 108.5 | 115% | 111.4 | 112% |
| ALL | out 9m+ | back | 1296 | 397 | 126 | 123.9 | 102% | 121.7 | 104% |
| Geelong | true | lead | 76 | 76 | 9 | 8.2 | 110% | 8.1 | 111% |
| Geelong | true | on pace | 210 | 76 | 24 | 21.2 | 113% | 19.9 | 120% |
| Geelong | true | midfield | 234 | 76 | 18 | 22.2 | 81% | 23.6 | 76% |
| Geelong | true | back | 261 | 76 | 25 | 24.4 | 102% | 24.4 | 103% |
| Geelong | out 1-4m | lead | 37 | 37 | 5 | 3.2 | 157% | 4.2 | 119% |
| Geelong | out 1-4m | on pace | 94 | 37 | 11 | 12.5 | 88% | 10.9 | 101% |
| Geelong | out 1-4m | midfield | 107 | 37 | 13 | 11.2 | 116% | 10.7 | 122% |
| Geelong | out 1-4m | back | 118 | 37 | 8 | 10.1 | 79% | 11.2 | 71% |
| Geelong | out 5-8m | lead | 71 | 71 | 16 | 9.9 | 161% | 9.1 | 177% |
| Geelong | out 5-8m | on pace | 175 | 71 | 22 | 19.2 | 114% | 19.4 | 113% |
| Geelong | out 5-8m | midfield | 204 | 71 | 19 | 19.7 | 97% | 20.7 | 92% |
| Geelong | out 5-8m | back | 226 | 71 | 14 | 22.2 | 63% | 21.8 | 64% |
| Geelong | out 9m+ | lead | 62 | 62 | 9 | 10.0 | 90% | 9.2 | 98% |
| Geelong | out 9m+ | on pace | 161 | 62 | 14 | 16.8 | 83% | 17.3 | 81% |
| Geelong | out 9m+ | midfield | 180 | 62 | 19 | 16.6 | 114% | 17.2 | 110% |
| Geelong | out 9m+ | back | 196 | 62 | 20 | 18.6 | 108% | 18.3 | 109% |
| Caulfield | true | lead | 77 | 77 | 10 | 10.3 | 98% | 9.2 | 108% |
| Caulfield | true | on pace | 207 | 77 | 23 | 21.2 | 109% | 19.9 | 116% |
| Caulfield | true | midfield | 238 | 77 | 19 | 21.9 | 87% | 22.9 | 83% |
| Caulfield | true | back | 259 | 77 | 25 | 23.7 | 106% | 25.0 | 100% |
| Caulfield | out 1-4m | lead | 58 | 58 | 4 | 7.7 | 52% | 7.0 | 57% |
| Caulfield | out 1-4m | on pace | 170 | 58 | 14 | 16.8 | 83% | 15.8 | 88% |
| Caulfield | out 1-4m | midfield | 191 | 58 | 23 | 17.2 | 133% | 17.6 | 131% |
| Caulfield | out 1-4m | back | 210 | 58 | 17 | 16.3 | 104% | 17.6 | 97% |
| Caulfield | out 5-8m | lead | 49 | 49 | 11 | 6.6 | 167% | 5.8 | 189% |
| Caulfield | out 5-8m | on pace | 137 | 49 | 11 | 13.7 | 80% | 13.4 | 82% |
| Caulfield | out 5-8m | midfield | 153 | 49 | 12 | 12.4 | 97% | 13.0 | 92% |
| Caulfield | out 5-8m | back | 171 | 49 | 15 | 16.3 | 92% | 16.8 | 89% |
| Caulfield | out 9m+ | lead | 60 | 60 | 8 | 8.0 | 100% | 7.1 | 112% |
| Caulfield | out 9m+ | on pace | 164 | 61 | 22 | 18.4 | 119% | 17.9 | 123% |
| Caulfield | out 9m+ | midfield | 186 | 61 | 16 | 16.1 | 99% | 17.2 | 93% |
| Caulfield | out 9m+ | back | 206 | 61 | 15 | 18.5 | 81% | 18.7 | 80% |
| Ballarat Synthetic | true | lead | 213 | 213 | 35 | 31.0 | 113% | 28.0 | 125% |
| Ballarat Synthetic | true | on pace | 502 | 213 | 65 | 62.8 | 103% | 58.8 | 111% |
| Ballarat Synthetic | true | midfield | 595 | 213 | 57 | 61.9 | 92% | 65.7 | 87% |
| Ballarat Synthetic | true | back | 666 | 213 | 56 | 57.3 | 98% | 60.4 | 93% |
| Cranbourne | true | lead | 79 | 79 | 8 | 12.5 | 64% | 11.3 | 71% |
| Cranbourne | true | on pace | 164 | 81 | 22 | 20.5 | 107% | 19.9 | 111% |
| Cranbourne | true | midfield | 200 | 82 | 23 | 21.8 | 106% | 23.4 | 98% |
| Cranbourne | true | back | 247 | 82 | 29 | 27.2 | 106% | 27.4 | 106% |
| Cranbourne | out 1-4m | lead | 54 | 54 | 7 | 7.9 | 89% | 7.2 | 97% |
| Cranbourne | out 1-4m | on pace | 132 | 54 | 12 | 14.4 | 83% | 14.6 | 82% |
| Cranbourne | out 1-4m | midfield | 145 | 54 | 15 | 15.7 | 96% | 16.0 | 93% |
| Cranbourne | out 1-4m | back | 166 | 54 | 20 | 16.0 | 125% | 16.1 | 124% |
| Cranbourne | out 5-8m | lead | 56 | 56 | 11 | 9.0 | 122% | 7.8 | 140% |
| Cranbourne | out 5-8m | on pace | 119 | 56 | 17 | 15.7 | 108% | 15.3 | 111% |
| Cranbourne | out 5-8m | midfield | 143 | 56 | 15 | 17.0 | 88% | 17.1 | 88% |
| Cranbourne | out 5-8m | back | 156 | 56 | 13 | 14.3 | 91% | 15.8 | 82% |
| Cranbourne | out 9m+ | lead | 30 | 30 | 7 | 5.4 | 129% | 5.1 | 136% |
| Cranbourne | out 9m+ | on pace | 58 | 30 | 6 | 7.4 | 82% | 8.3 | 72% |
| Cranbourne | out 9m+ | midfield | 68 | 30 | 10 | 9.4 | 106% | 9.1 | 110% |
| Cranbourne | out 9m+ | back | 76 | 30 | 7 | 7.8 | 90% | 7.4 | 94% |
| Flemington | true | lead | 65 | 65 | 10 | 8.3 | 121% | 7.4 | 135% |
| Flemington | true | on pace | 194 | 65 | 16 | 19.0 | 84% | 18.4 | 87% |
| Flemington | true | midfield | 218 | 65 | 19 | 19.0 | 100% | 19.8 | 96% |
| Flemington | true | back | 240 | 65 | 20 | 18.7 | 107% | 19.4 | 103% |
| Flemington | out 1-4m | lead | 54 | 54 | 8 | 5.7 | 141% | 5.5 | 146% |
| Flemington | out 1-4m | on pace | 176 | 54 | 14 | 16.6 | 85% | 16.1 | 87% |
| Flemington | out 1-4m | midfield | 194 | 54 | 16 | 14.4 | 111% | 15.8 | 101% |
| Flemington | out 1-4m | back | 218 | 54 | 16 | 17.4 | 92% | 16.6 | 96% |
| Flemington | out 5-8m | lead | 37 | 37 | 3 | 3.9 | 76% | 4.2 | 72% |
| Flemington | out 5-8m | on pace | 107 | 37 | 10 | 10.4 | 96% | 10.1 | 99% |
| Flemington | out 5-8m | midfield | 122 | 37 | 12 | 10.1 | 119% | 10.5 | 114% |
| Flemington | out 5-8m | back | 134 | 37 | 12 | 12.6 | 95% | 12.2 | 98% |
| Flemington | out 9m+ | lead | 64 | 64 | 5 | 7.2 | 69% | 6.8 | 74% |
| Flemington | out 9m+ | on pace | 195 | 64 | 15 | 17.5 | 86% | 17.4 | 86% |
| Flemington | out 9m+ | midfield | 214 | 64 | 30 | 18.9 | 159% | 18.8 | 160% |
| Flemington | out 9m+ | back | 234 | 64 | 14 | 20.4 | 69% | 21.0 | 67% |
| Pakenham Park | true | lead | 47 | 47 | 4 | 7.0 | 57% | 7.0 | 57% |
| Pakenham Park | true | on pace | 100 | 47 | 13 | 12.2 | 106% | 13.1 | 99% |
| Pakenham Park | true | midfield | 122 | 47 | 19 | 16.1 | 118% | 15.0 | 127% |
| Pakenham Park | true | back | 138 | 47 | 11 | 11.6 | 95% | 11.9 | 93% |
| Pakenham Park | out 1-4m | lead | 65 | 65 | 8 | 8.5 | 94% | 8.9 | 90% |
| Pakenham Park | out 1-4m | on pace | 156 | 65 | 18 | 15.7 | 115% | 17.3 | 104% |
| Pakenham Park | out 1-4m | midfield | 180 | 65 | 21 | 20.5 | 103% | 19.2 | 110% |
| Pakenham Park | out 1-4m | back | 202 | 65 | 18 | 20.3 | 89% | 19.6 | 92% |
| Pakenham Park | out 5-8m | lead | 72 | 72 | 7 | 8.9 | 79% | 9.4 | 75% |
| Pakenham Park | out 5-8m | on pace | 168 | 72 | 23 | 20.3 | 114% | 20.8 | 111% |
| Pakenham Park | out 5-8m | midfield | 189 | 72 | 22 | 23.1 | 95% | 22.4 | 98% |
| Pakenham Park | out 5-8m | back | 213 | 72 | 20 | 19.7 | 101% | 19.5 | 103% |
| Pakenham Park | out 9m+ | lead | 31 | 31 | 9 | 5.1 | 176% | 4.7 | 190% |
| Pakenham Park | out 9m+ | on pace | 74 | 31 | 7 | 8.0 | 87% | 8.1 | 86% |
| Pakenham Park | out 9m+ | midfield | 86 | 31 | 7 | 7.5 | 93% | 8.0 | 87% |
| Pakenham Park | out 9m+ | back | 97 | 31 | 8 | 10.4 | 77% | 10.1 | 79% |
| Sandown Hillside | true | on pace | 68 | 29 | 14 | 9.1 | 153% | 8.4 | 168% |
| Sandown Hillside | true | midfield | 81 | 29 | 5 | 7.6 | 66% | 8.1 | 62% |
| Sandown Hillside | true | back | 87 | 29 | 9 | 8.9 | 101% | 9.1 | 99% |
| Sandown Hillside | out 1-4m | on pace | 32 | 16 | 3 | 3.5 | 85% | 3.7 | 81% |
| Sandown Hillside | out 1-4m | midfield | 39 | 16 | 8 | 4.7 | 170% | 4.7 | 170% |
| Sandown Hillside | out 1-4m | back | 45 | 16 | 3 | 4.7 | 64% | 4.6 | 65% |
| Sandown Hillside | out 5-8m | lead | 74 | 74 | 5 | 9.0 | 56% | 8.6 | 58% |
| Sandown Hillside | out 5-8m | on pace | 182 | 74 | 24 | 19.6 | 123% | 20.5 | 117% |
| Sandown Hillside | out 5-8m | midfield | 208 | 74 | 20 | 19.8 | 101% | 20.6 | 97% |
| Sandown Hillside | out 5-8m | back | 237 | 74 | 25 | 25.6 | 98% | 24.3 | 103% |
| Sandown Hillside | out 9m+ | lead | 64 | 64 | 8 | 7.8 | 103% | 7.0 | 115% |
| Sandown Hillside | out 9m+ | on pace | 165 | 64 | 12 | 16.8 | 71% | 17.8 | 68% |
| Sandown Hillside | out 9m+ | midfield | 185 | 64 | 17 | 18.8 | 91% | 19.1 | 89% |
| Sandown Hillside | out 9m+ | back | 204 | 64 | 27 | 20.6 | 131% | 20.2 | 134% |
| Warrnambool | true | lead | 84 | 84 | 8 | 11.6 | 69% | 12.1 | 66% |
| Warrnambool | true | on pace | 233 | 83 | 27 | 22.0 | 123% | 23.1 | 117% |
| Warrnambool | true | midfield | 260 | 84 | 22 | 24.1 | 91% | 24.3 | 90% |
| Warrnambool | true | back | 291 | 84 | 27 | 26.4 | 102% | 24.5 | 110% |
| Warrnambool | out 1-4m | lead | 55 | 55 | 10 | 8.8 | 114% | 8.6 | 117% |
| Warrnambool | out 1-4m | on pace | 139 | 55 | 14 | 13.9 | 100% | 14.6 | 96% |
| Warrnambool | out 1-4m | midfield | 164 | 55 | 16 | 15.5 | 103% | 15.8 | 101% |
| Warrnambool | out 1-4m | back | 178 | 55 | 15 | 16.8 | 89% | 16.0 | 94% |
| Warrnambool | out 5-8m | lead | 38 | 38 | 3 | 4.7 | 64% | 5.4 | 56% |
| Warrnambool | out 5-8m | on pace | 89 | 37 | 13 | 10.5 | 123% | 11.1 | 117% |
| Warrnambool | out 5-8m | midfield | 104 | 38 | 10 | 11.5 | 87% | 10.8 | 93% |
| Warrnambool | out 5-8m | back | 116 | 38 | 12 | 11.3 | 107% | 10.8 | 112% |
| Bendigo | true | lead | 66 | 66 | 4 | 8.9 | 45% | 7.6 | 53% |
| Bendigo | true | on pace | 189 | 67 | 20 | 21.3 | 94% | 19.5 | 103% |
| Bendigo | true | midfield | 209 | 67 | 20 | 18.9 | 106% | 20.3 | 99% |
| Bendigo | true | back | 241 | 67 | 23 | 18.0 | 128% | 19.7 | 117% |
| Bendigo | out 1-4m | lead | 34 | 34 | 5 | 4.2 | 120% | 4.0 | 127% |
| Bendigo | out 1-4m | on pace | 92 | 33 | 9 | 10.2 | 89% | 9.4 | 96% |
| Bendigo | out 1-4m | midfield | 104 | 34 | 11 | 9.3 | 119% | 9.6 | 114% |
| Bendigo | out 1-4m | back | 117 | 34 | 9 | 10.4 | 86% | 11.1 | 81% |
| Bendigo | out 5-8m | lead | 38 | 38 | 6 | 6.7 | 89% | 6.2 | 98% |
| Bendigo | out 5-8m | on pace | 101 | 39 | 12 | 11.6 | 103% | 10.9 | 110% |
| Bendigo | out 5-8m | midfield | 112 | 38 | 10 | 9.0 | 112% | 9.9 | 101% |
| Bendigo | out 5-8m | back | 141 | 39 | 11 | 11.7 | 94% | 12.1 | 91% |
| Bendigo | out 9m+ | lead | 32 | 32 | 4 | 4.9 | 81% | 4.7 | 84% |
| Bendigo | out 9m+ | on pace | 82 | 31 | 3 | 9.0 | 33% | 9.0 | 33% |
| Bendigo | out 9m+ | midfield | 97 | 31 | 17 | 8.5 | 201% | 8.4 | 203% |
| Bendigo | out 9m+ | back | 105 | 32 | 8 | 9.6 | 83% | 9.9 | 81% |
| Sale | true | lead | 83 | 83 | 16 | 13.4 | 119% | 13.1 | 122% |
| Sale | true | on pace | 202 | 83 | 17 | 22.1 | 77% | 23.2 | 73% |
| Sale | true | midfield | 223 | 83 | 23 | 23.0 | 100% | 22.5 | 102% |
| Sale | true | back | 258 | 83 | 27 | 24.6 | 110% | 24.3 | 111% |
| Sale | out 1-4m | lead | 37 | 37 | 10 | 6.3 | 160% | 6.0 | 166% |
| Sale | out 1-4m | on pace | 94 | 37 | 9 | 10.9 | 82% | 11.2 | 80% |
| Sale | out 1-4m | midfield | 106 | 37 | 7 | 8.5 | 83% | 8.2 | 85% |
| Sale | out 1-4m | back | 115 | 37 | 11 | 11.4 | 97% | 11.6 | 95% |
| Sale | out 5-8m | lead | 48 | 48 | 8 | 7.8 | 102% | 6.6 | 122% |
| Sale | out 5-8m | on pace | 122 | 48 | 12 | 11.8 | 101% | 12.3 | 97% |
| Sale | out 5-8m | midfield | 136 | 48 | 13 | 12.4 | 105% | 14.2 | 91% |
| Sale | out 5-8m | back | 159 | 48 | 15 | 15.9 | 94% | 14.9 | 101% |
| Mornington | true | lead | 58 | 58 | 7 | 7.4 | 95% | 6.6 | 107% |
| Mornington | true | on pace | 148 | 59 | 19 | 17.9 | 106% | 16.4 | 116% |
| Mornington | true | midfield | 168 | 60 | 18 | 15.3 | 117% | 16.7 | 108% |
| Mornington | true | back | 200 | 60 | 16 | 19.3 | 83% | 20.3 | 79% |
| Mornington | out 1-4m | on pace | 48 | 23 | 8 | 5.9 | 135% | 6.3 | 127% |
| Mornington | out 1-4m | midfield | 55 | 23 | 8 | 6.6 | 122% | 6.3 | 126% |
| Mornington | out 1-4m | back | 60 | 23 | 4 | 7.2 | 56% | 6.7 | 60% |
| Mornington | out 5-8m | lead | 79 | 79 | 16 | 13.3 | 120% | 11.7 | 137% |
| Mornington | out 5-8m | on pace | 192 | 79 | 22 | 19.6 | 112% | 19.7 | 112% |
| Mornington | out 5-8m | midfield | 229 | 79 | 21 | 21.7 | 97% | 23.5 | 90% |
| Mornington | out 5-8m | back | 257 | 79 | 20 | 24.4 | 82% | 24.2 | 83% |
| Seymour | true | lead | 69 | 69 | 8 | 7.6 | 105% | 7.6 | 105% |
| Seymour | true | on pace | 222 | 69 | 15 | 20.5 | 73% | 20.4 | 74% |
| Seymour | true | midfield | 238 | 69 | 25 | 21.9 | 114% | 21.7 | 115% |
| Seymour | true | back | 262 | 69 | 21 | 19.0 | 111% | 19.3 | 109% |
| Seymour | out 1-4m | lead | 31 | 31 | 4 | 4.1 | 97% | 4.5 | 89% |
| Seymour | out 1-4m | on pace | 87 | 30 | 4 | 7.9 | 51% | 7.8 | 51% |
| Seymour | out 1-4m | midfield | 96 | 31 | 14 | 9.2 | 152% | 9.7 | 145% |
| Seymour | out 1-4m | back | 108 | 31 | 9 | 9.7 | 93% | 9.1 | 99% |
| Seymour | out 5-8m | lead | 56 | 56 | 3 | 7.4 | 41% | 7.4 | 41% |
| Seymour | out 5-8m | on pace | 145 | 56 | 14 | 14.2 | 99% | 15.1 | 93% |
| Seymour | out 5-8m | midfield | 162 | 56 | 19 | 17.0 | 112% | 16.6 | 114% |
| Seymour | out 5-8m | back | 181 | 56 | 20 | 17.4 | 115% | 16.8 | 119% |
| Ballarat | true | lead | 59 | 59 | 6 | 6.8 | 88% | 6.7 | 89% |
| Ballarat | true | on pace | 167 | 60 | 17 | 18.5 | 92% | 17.9 | 95% |
| Ballarat | true | midfield | 183 | 60 | 21 | 16.4 | 128% | 16.9 | 125% |
| Ballarat | true | back | 229 | 60 | 16 | 18.3 | 88% | 18.5 | 86% |
| Ballarat | out 1-4m | on pace | 57 | 20 | 7 | 7.0 | 99% | 6.4 | 110% |
| Ballarat | out 1-4m | midfield | 65 | 21 | 6 | 6.0 | 99% | 5.9 | 102% |
| Ballarat | out 1-4m | back | 83 | 21 | 6 | 6.1 | 98% | 6.3 | 96% |
| Ballarat | out 5-8m | lead | 32 | 32 | 3 | 3.0 | 100% | 3.4 | 88% |
| Ballarat | out 5-8m | on pace | 75 | 32 | 8 | 9.5 | 84% | 9.3 | 86% |
| Ballarat | out 5-8m | midfield | 85 | 32 | 13 | 9.5 | 137% | 9.5 | 138% |
| Ballarat | out 5-8m | back | 96 | 32 | 8 | 10.0 | 80% | 9.8 | 82% |
| Ballarat | out 9m+ | lead | 32 | 32 | 3 | 4.0 | 74% | 4.1 | 72% |
| Ballarat | out 9m+ | on pace | 81 | 32 | 7 | 10.0 | 70% | 10.5 | 66% |
| Ballarat | out 9m+ | midfield | 86 | 32 | 5 | 7.1 | 71% | 7.5 | 67% |
| Ballarat | out 9m+ | back | 103 | 32 | 17 | 10.9 | 156% | 9.8 | 173% |
| Moe | true | lead | 78 | 78 | 11 | 8.4 | 132% | 9.2 | 119% |
| Moe | true | on pace | 218 | 78 | 22 | 22.9 | 96% | 21.9 | 101% |
| Moe | true | midfield | 241 | 78 | 20 | 20.9 | 96% | 21.7 | 92% |
| Moe | true | back | 286 | 78 | 25 | 25.8 | 97% | 25.2 | 99% |
| Moe | out 1-4m | lead | 32 | 32 | 3 | 4.2 | 71% | 3.8 | 79% |
| Moe | out 1-4m | on pace | 93 | 32 | 11 | 9.7 | 114% | 9.8 | 113% |
| Moe | out 1-4m | midfield | 99 | 32 | 9 | 8.0 | 113% | 9.5 | 95% |
| Moe | out 1-4m | back | 108 | 32 | 9 | 10.1 | 89% | 9.0 | 100% |
| Moe | out 5-8m | on pace | 71 | 29 | 7 | 8.7 | 80% | 8.8 | 80% |
| Moe | out 5-8m | midfield | 84 | 29 | 8 | 8.1 | 99% | 7.8 | 102% |
| Moe | out 5-8m | back | 92 | 29 | 7 | 7.4 | 94% | 7.6 | 93% |
| Pakenham Synthetic | true | lead | 130 | 130 | 13 | 15.3 | 85% | 15.2 | 85% |
| Pakenham Synthetic | true | on pace | 357 | 131 | 40 | 35.9 | 112% | 35.5 | 113% |
| Pakenham Synthetic | true | midfield | 415 | 131 | 41 | 39.6 | 104% | 40.2 | 102% |
| Pakenham Synthetic | true | back | 470 | 131 | 37 | 40.3 | 92% | 40.1 | 92% |
| Sandown Lakeside | true | lead | 50 | 50 | 3 | 5.1 | 59% | 5.0 | 60% |
| Sandown Lakeside | true | on pace | 137 | 50 | 17 | 14.5 | 118% | 14.9 | 114% |
| Sandown Lakeside | true | midfield | 155 | 50 | 14 | 15.6 | 90% | 15.5 | 90% |
| Sandown Lakeside | true | back | 167 | 50 | 16 | 14.8 | 108% | 14.5 | 110% |
| Sandown Lakeside | out 1-4m | lead | 40 | 40 | 7 | 6.4 | 109% | 5.5 | 127% |
| Sandown Lakeside | out 1-4m | on pace | 100 | 40 | 13 | 10.0 | 130% | 10.2 | 127% |
| Sandown Lakeside | out 1-4m | midfield | 118 | 40 | 13 | 11.8 | 110% | 12.5 | 104% |
| Sandown Lakeside | out 1-4m | back | 123 | 40 | 7 | 11.8 | 59% | 11.7 | 60% |
| Sandown Lakeside | out 5-8m | lead | 32 | 32 | 0 | 3.3 | 0% | 3.2 | 0% |
| Sandown Lakeside | out 5-8m | on pace | 79 | 32 | 6 | 6.4 | 93% | 7.0 | 85% |
| Sandown Lakeside | out 5-8m | midfield | 96 | 32 | 12 | 10.7 | 112% | 10.5 | 114% |
| Sandown Lakeside | out 5-8m | back | 103 | 32 | 14 | 11.6 | 120% | 11.3 | 124% |
| Echuca | true | lead | 117 | 117 | 15 | 17.4 | 86% | 16.2 | 93% |
| Echuca | true | on pace | 330 | 119 | 25 | 31.6 | 79% | 31.6 | 79% |
| Echuca | true | midfield | 381 | 119 | 28 | 36.0 | 78% | 37.1 | 75% |
| Echuca | true | back | 430 | 119 | 51 | 34.0 | 150% | 34.0 | 150% |
| Wangaratta | true | lead | 59 | 59 | 8 | 7.4 | 108% | 6.9 | 116% |
| Wangaratta | true | on pace | 192 | 59 | 24 | 18.0 | 133% | 18.5 | 130% |
| Wangaratta | true | midfield | 214 | 59 | 9 | 17.3 | 52% | 17.7 | 51% |
| Wangaratta | true | back | 240 | 59 | 18 | 16.3 | 110% | 15.9 | 113% |
| Wangaratta | out 1-4m | lead | 58 | 58 | 8 | 7.1 | 113% | 7.0 | 115% |
| Wangaratta | out 1-4m | on pace | 171 | 58 | 23 | 18.0 | 128% | 18.7 | 123% |
| Wangaratta | out 1-4m | midfield | 185 | 58 | 10 | 17.7 | 56% | 17.0 | 59% |
| Wangaratta | out 1-4m | back | 214 | 58 | 17 | 15.3 | 111% | 15.4 | 111% |
| Kilmore | true | lead | 62 | 62 | 9 | 8.5 | 105% | 8.3 | 109% |
| Kilmore | true | on pace | 160 | 62 | 17 | 19.4 | 88% | 18.9 | 90% |
| Kilmore | true | midfield | 182 | 62 | 20 | 15.6 | 128% | 17.1 | 117% |
| Kilmore | true | back | 218 | 62 | 16 | 18.4 | 87% | 17.7 | 90% |
| Kilmore | out 1-4m | lead | 31 | 31 | 6 | 4.4 | 136% | 3.6 | 167% |
| Kilmore | out 1-4m | on pace | 85 | 31 | 6 | 8.6 | 70% | 9.8 | 61% |
| Kilmore | out 1-4m | midfield | 95 | 31 | 11 | 9.6 | 115% | 9.3 | 118% |
| Kilmore | out 1-4m | back | 102 | 31 | 8 | 8.4 | 95% | 8.3 | 96% |
| Kilmore | out 5-8m | on pace | 40 | 16 | 3 | 5.0 | 59% | 5.6 | 53% |
| Kilmore | out 5-8m | midfield | 45 | 16 | 2 | 4.8 | 42% | 4.0 | 50% |
| Kilmore | out 5-8m | back | 49 | 16 | 5 | 4.0 | 126% | 3.9 | 127% |
| Caulfield Heath | true | lead | 41 | 41 | 5 | 5.3 | 94% | 4.8 | 105% |
| Caulfield Heath | true | on pace | 88 | 41 | 10 | 9.7 | 103% | 10.3 | 97% |
| Caulfield Heath | true | midfield | 99 | 41 | 14 | 12.7 | 110% | 13.1 | 107% |
| Caulfield Heath | true | back | 116 | 41 | 12 | 13.2 | 91% | 12.9 | 93% |
| Caulfield Heath | out 1-4m | lead | 49 | 49 | 8 | 7.4 | 108% | 6.5 | 122% |
| Caulfield Heath | out 1-4m | on pace | 109 | 49 | 7 | 11.4 | 61% | 11.3 | 62% |
| Caulfield Heath | out 1-4m | midfield | 127 | 49 | 15 | 14.8 | 101% | 15.3 | 98% |
| Caulfield Heath | out 1-4m | back | 142 | 49 | 19 | 15.4 | 124% | 15.9 | 120% |
| Caulfield Heath | out 5-8m | on pace | 36 | 16 | 5 | 4.3 | 115% | 4.6 | 109% |
| Caulfield Heath | out 5-8m | midfield | 42 | 16 | 3 | 4.9 | 61% | 4.8 | 62% |
| Caulfield Heath | out 5-8m | back | 48 | 16 | 5 | 4.5 | 111% | 4.7 | 107% |
| Swan Hill | true | lead | 93 | 93 | 13 | 12.6 | 103% | 11.5 | 113% |
| Swan Hill | true | on pace | 280 | 94 | 23 | 24.2 | 95% | 25.7 | 90% |
| Swan Hill | true | midfield | 304 | 94 | 22 | 26.3 | 84% | 26.6 | 83% |
| Swan Hill | true | back | 360 | 94 | 36 | 30.8 | 117% | 30.2 | 119% |
| Wodonga | true | lead | 68 | 68 | 10 | 9.6 | 105% | 8.7 | 115% |
| Wodonga | true | on pace | 183 | 68 | 24 | 21.8 | 110% | 21.5 | 112% |
| Wodonga | true | midfield | 209 | 68 | 15 | 19.8 | 76% | 19.4 | 77% |
| Wodonga | true | back | 236 | 68 | 19 | 16.9 | 113% | 18.4 | 104% |
| Wodonga | out 1-4m | lead | 30 | 30 | 5 | 4.1 | 121% | 3.8 | 132% |
| Wodonga | out 1-4m | on pace | 71 | 30 | 8 | 8.3 | 96% | 8.2 | 97% |
| Wodonga | out 1-4m | midfield | 82 | 30 | 5 | 9.6 | 52% | 9.6 | 52% |
| Wodonga | out 1-4m | back | 93 | 30 | 12 | 7.9 | 151% | 8.4 | 143% |
| Kyneton | out 1-4m | lead | 50 | 50 | 5 | 6.1 | 82% | 5.2 | 96% |
| Kyneton | out 1-4m | on pace | 126 | 50 | 21 | 14.7 | 143% | 15.8 | 133% |
| Kyneton | out 1-4m | midfield | 150 | 50 | 13 | 15.6 | 83% | 15.8 | 82% |
| Kyneton | out 1-4m | back | 161 | 50 | 11 | 13.6 | 81% | 13.2 | 83% |
| Kyneton | out 5-8m | lead | 33 | 33 | 6 | 5.2 | 115% | 5.0 | 120% |
| Kyneton | out 5-8m | on pace | 80 | 33 | 6 | 7.9 | 76% | 8.7 | 69% |
| Kyneton | out 5-8m | midfield | 97 | 33 | 12 | 10.7 | 112% | 10.2 | 117% |
| Kyneton | out 5-8m | back | 103 | 33 | 9 | 9.2 | 98% | 9.1 | 99% |
| Bairnsdale | true | lead | 58 | 58 | 8 | 9.8 | 82% | 8.5 | 94% |
| Bairnsdale | true | on pace | 176 | 58 | 20 | 16.2 | 123% | 16.1 | 125% |
| Bairnsdale | true | midfield | 196 | 58 | 18 | 15.7 | 114% | 16.4 | 110% |
| Bairnsdale | true | back | 216 | 58 | 12 | 16.3 | 74% | 17.1 | 70% |
| Bairnsdale | out 1-4m | on pace | 42 | 15 | 5 | 4.1 | 123% | 4.2 | 120% |
| Bairnsdale | out 1-4m | midfield | 49 | 15 | 6 | 5.0 | 120% | 4.7 | 127% |
| Bairnsdale | out 1-4m | back | 60 | 15 | 2 | 4.7 | 42% | 4.7 | 42% |
| Mildura | true | lead | 72 | 72 | 9 | 11.1 | 81% | 10.4 | 87% |
| Mildura | true | on pace | 189 | 72 | 16 | 21.4 | 75% | 21.4 | 75% |
| Mildura | true | midfield | 211 | 72 | 23 | 19.1 | 120% | 20.1 | 114% |
| Mildura | true | back | 242 | 72 | 24 | 20.3 | 118% | 20.1 | 119% |
| Hamilton | true | lead | 67 | 67 | 14 | 10.4 | 135% | 9.8 | 143% |
| Hamilton | true | on pace | 156 | 67 | 25 | 20.7 | 121% | 20.1 | 124% |
| Hamilton | true | midfield | 176 | 67 | 13 | 18.1 | 72% | 18.5 | 70% |
| Hamilton | true | back | 197 | 67 | 15 | 17.9 | 84% | 18.5 | 81% |
| Werribee | true | on pace | 60 | 22 | 5 | 6.8 | 74% | 6.9 | 73% |
| Werribee | true | midfield | 72 | 22 | 9 | 6.9 | 131% | 6.9 | 130% |
| Werribee | true | back | 77 | 22 | 6 | 6.8 | 89% | 6.2 | 97% |
| Werribee | out 1-4m | on pace | 42 | 15 | 4 | 4.3 | 92% | 4.2 | 96% |
| Werribee | out 1-4m | midfield | 46 | 15 | 7 | 5.2 | 134% | 5.1 | 138% |
| Werribee | out 1-4m | back | 52 | 15 | 2 | 3.1 | 65% | 3.8 | 53% |
| Werribee | out 5-8m | on pace | 65 | 23 | 6 | 7.0 | 86% | 6.5 | 92% |
| Werribee | out 5-8m | midfield | 69 | 23 | 8 | 6.9 | 115% | 7.5 | 107% |
| Werribee | out 5-8m | back | 74 | 23 | 8 | 6.3 | 126% | 6.1 | 131% |
| Moonee Valley | true | lead | 37 | 37 | 4 | 4.6 | 87% | 4.5 | 88% |
| Moonee Valley | true | on pace | 90 | 37 | 6 | 8.4 | 71% | 8.6 | 70% |
| Moonee Valley | true | midfield | 101 | 37 | 9 | 11.5 | 78% | 11.9 | 75% |
| Moonee Valley | true | back | 121 | 37 | 18 | 12.5 | 143% | 11.9 | 151% |
| Moonee Valley | out 5-8m | on pace | 36 | 17 | 3 | 4.1 | 74% | 4.0 | 75% |
| Moonee Valley | out 5-8m | midfield | 46 | 17 | 5 | 4.7 | 107% | 5.1 | 99% |
| Moonee Valley | out 5-8m | back | 47 | 17 | 2 | 5.0 | 40% | 5.4 | 37% |
| Yarra Valley | true | lead | 31 | 31 | 2 | 4.3 | 47% | 4.0 | 49% |
| Yarra Valley | true | on pace | 80 | 31 | 7 | 8.6 | 81% | 9.6 | 73% |
| Yarra Valley | true | midfield | 96 | 31 | 14 | 10.5 | 133% | 10.3 | 136% |
| Yarra Valley | true | back | 107 | 31 | 8 | 7.6 | 105% | 7.0 | 114% |
| Yarra Valley | out 1-4m | lead | 31 | 31 | 7 | 5.4 | 129% | 4.9 | 142% |
| Yarra Valley | out 1-4m | on pace | 83 | 31 | 8 | 9.6 | 83% | 9.3 | 86% |
| Yarra Valley | out 1-4m | midfield | 88 | 31 | 8 | 7.6 | 105% | 8.3 | 96% |
| Yarra Valley | out 1-4m | back | 92 | 31 | 8 | 8.4 | 96% | 8.5 | 94% |
| Donald | true | lead | 53 | 53 | 9 | 7.9 | 115% | 7.0 | 128% |
| Donald | true | on pace | 147 | 53 | 13 | 15.4 | 85% | 15.7 | 83% |
| Donald | true | midfield | 161 | 53 | 15 | 13.9 | 108% | 14.9 | 100% |
| Donald | true | back | 188 | 53 | 16 | 15.9 | 101% | 15.4 | 104% |
