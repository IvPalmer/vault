import { useState, useMemo } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  flexRender,
} from '@tanstack/react-table'
import styles from './VaultTable.module.css'

/**
 * VaultTable — shared TanStack React Table wrapper.
 * Features: sort, search, fixed height, semantic colors.
 *
 * Props:
 *   columns - TanStack column definitions
 *   data - array of row objects
 *   emptyMessage - string when no data
 *   searchable - enable global search box
 *   maxHeight - max table height in px (default 500)
 *   compact - use compact row height
 */
function VaultTable({
  columns,
  data,
  emptyMessage = 'Nenhum dado disponível.',
  searchable = true,
  maxHeight = 500,
  compact = false,
  rowClassName,
}) {
  const [sorting, setSorting] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')

  const table = useReactTable({
    data,
    columns,
    state: { sorting, globalFilter },
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: 'includesString',
  })

  if (!data || data.length === 0) {
    return <div className={styles.empty}>{emptyMessage}</div>
  }

  return (
    <div className={styles.wrapper}>
      {searchable && data.length > 5 && (
        <div className={styles.searchBar}>
          <input
            type="text"
            value={globalFilter}
            onChange={(e) => setGlobalFilter(e.target.value)}
            placeholder="Buscar..."
            className={styles.searchInput}
          />
          {globalFilter && (
            <button
              className={styles.clearBtn}
              onClick={() => setGlobalFilter('')}
            >
              ×
            </button>
          )}
        </div>
      )}

      <div className={styles.tableContainer} style={{ maxHeight }}>
        <table className={`${styles.table} ${compact ? styles.compact : ''}`}>
          <thead className={styles.thead}>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className={`${styles.th} ${
                      header.column.getCanSort() ? styles.sortable : ''
                    }`}
                    style={{
                      width: header.column.columnDef.size,
                      minWidth: header.column.columnDef.minSize,
                      maxWidth: header.column.columnDef.maxSize,
                    }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <span className={styles.headerContent}>
                      {flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && ' ▲'}
                      {header.column.getIsSorted() === 'desc' && ' ▼'}
                    </span>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className={styles.tbody}>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className={`${styles.tr} ${rowClassName ? rowClassName(row) : ''}`}>
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className={styles.td}
                    style={{
                      width: cell.column.columnDef.size,
                      minWidth: cell.column.columnDef.minSize,
                      maxWidth: cell.column.columnDef.maxSize,
                    }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className={styles.footer}>
        {table.getFilteredRowModel().rows.length} de {data.length} itens
      </div>
    </div>
  )
}

export default VaultTable
