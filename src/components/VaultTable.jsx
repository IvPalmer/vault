import { useState, useMemo, useCallback, useRef } from 'react'
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
 * Features: sort, search, fixed height, semantic colors, drag-to-reorder rows.
 *
 * Props:
 *   columns - TanStack column definitions
 *   data - array of row objects
 *   emptyMessage - string when no data
 *   searchable - enable global search box
 *   maxHeight - max table height in px (default 500)
 *   compact - use compact row height
 *   rowClassName - fn(row) => className
 *   draggable - enable drag-to-reorder rows
 *   onReorder - fn(newData) called when rows are reordered
 */
function VaultTable({
  columns,
  data,
  emptyMessage = 'Nenhum dado disponível.',
  searchable = true,
  maxHeight = 500,
  compact = false,
  rowClassName,
  draggable = false,
  onReorder,
}) {
  const [sorting, setSorting] = useState([])
  const [globalFilter, setGlobalFilter] = useState('')
  const [dragRowIdx, setDragRowIdx] = useState(null)
  const [overRowIdx, setOverRowIdx] = useState(null)
  const dragNode = useRef(null)

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

  /* ── Drag handlers ── */
  const handleDragStart = useCallback((e, idx) => {
    setDragRowIdx(idx)
    dragNode.current = e.currentTarget
    e.currentTarget.classList.add(styles.draggingRow)
    e.dataTransfer.effectAllowed = 'move'
  }, [])

  const handleDragEnd = useCallback((e) => {
    e.currentTarget.classList.remove(styles.draggingRow)
    setDragRowIdx(null)
    setOverRowIdx(null)
    dragNode.current = null
  }, [])

  const handleDragOver = useCallback((e, idx) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setOverRowIdx(idx)
  }, [])

  const handleDragLeave = useCallback(() => {
    setOverRowIdx(null)
  }, [])

  const handleDrop = useCallback((e, targetIdx) => {
    e.preventDefault()
    if (dragRowIdx == null || dragRowIdx === targetIdx || !onReorder) {
      setOverRowIdx(null)
      return
    }
    const next = [...data]
    const [moved] = next.splice(dragRowIdx, 1)
    next.splice(targetIdx, 0, moved)
    onReorder(next)
    setOverRowIdx(null)
  }, [dragRowIdx, data, onReorder])

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
                {draggable && <th className={styles.th} style={{ width: 28 }} />}
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
            {table.getRowModel().rows.map((row, idx) => {
              const isOver = overRowIdx === idx && dragRowIdx !== idx
              return (
                <tr
                  key={row.id}
                  className={`${styles.tr} ${rowClassName ? rowClassName(row) : ''} ${isOver ? styles.dragOverRow : ''}`}
                  draggable={draggable}
                  onDragStart={draggable ? (e) => handleDragStart(e, idx) : undefined}
                  onDragEnd={draggable ? handleDragEnd : undefined}
                  onDragOver={draggable ? (e) => handleDragOver(e, idx) : undefined}
                  onDragLeave={draggable ? handleDragLeave : undefined}
                  onDrop={draggable ? (e) => handleDrop(e, idx) : undefined}
                >
                  {draggable && (
                    <td className={`${styles.td} ${styles.dragHandleCell}`}>
                      <span className={styles.dragGrip}>⠿</span>
                    </td>
                  )}
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
              )
            })}
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
