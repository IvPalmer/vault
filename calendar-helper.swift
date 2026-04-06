#!/usr/bin/env swift
//
// calendar-helper.swift — Native EventKit calendar reader (fast, no Calendar.app automation)
//
// Usage:
//   ./calendar-helper calendars               → list calendar names as JSON
//   ./calendar-helper events YYYY-MM-DD YYYY-MM-DD [cal1,cal2,...]  → events in range as JSON
//
import EventKit
import Foundation

let store = EKEventStore()
let semaphore = DispatchSemaphore(value: 0)

// Request access
if #available(macOS 14.0, *) {
    store.requestFullAccessToEvents { granted, error in
        semaphore.signal()
    }
} else {
    store.requestAccess(to: .event) { granted, error in
        semaphore.signal()
    }
}
semaphore.wait()

let args = CommandLine.arguments

if args.count < 2 {
    print("{\"error\": \"Usage: calendar-helper <calendars|events> [args...]\"}")
    exit(1)
}

let command = args[1]

if command == "calendars" {
    let calendars = store.calendars(for: .event)
    let names = calendars.map { $0.title }
    let data = try! JSONSerialization.data(withJSONObject: ["calendars": names])
    print(String(data: data, encoding: .utf8)!)
    exit(0)
}

if command == "events" {
    guard args.count >= 4 else {
        print("{\"error\": \"Usage: calendar-helper events YYYY-MM-DD YYYY-MM-DD [cal1,cal2,...]\"}")
        exit(1)
    }

    let dateFormatter = DateFormatter()
    dateFormatter.dateFormat = "yyyy-MM-dd"

    guard let startDate = dateFormatter.date(from: args[2]),
          let rawEnd = dateFormatter.date(from: args[3]) else {
        print("{\"error\": \"Invalid date format. Use YYYY-MM-DD\"}")
        exit(1)
    }
    let endDate = Calendar.current.date(bySettingHour: 23, minute: 59, second: 59, of: rawEnd)!

    // Filter calendars if specified
    var calendars: [EKCalendar]? = nil
    if args.count >= 5 && !args[4].isEmpty {
        let calNames = Set(args[4].components(separatedBy: ","))
        calendars = store.calendars(for: .event).filter { calNames.contains($0.title) }
        if calendars!.isEmpty {
            print("{\"events\": [], \"count\": 0}")
            exit(0)
        }
    }

    let predicate = store.predicateForEvents(withStart: startDate, end: endDate, calendars: calendars)
    let events = store.events(matching: predicate)

    let isoFormatter = DateFormatter()
    isoFormatter.dateFormat = "yyyy-MM-dd'T'HH:mm"

    let dateOnlyFormatter = DateFormatter()
    dateOnlyFormatter.dateFormat = "yyyy-MM-dd"

    var results: [[String: Any]] = []
    for event in events {
        var dict: [String: Any] = [
            "title": event.title ?? "",
            "start": event.isAllDay ? dateOnlyFormatter.string(from: event.startDate) : isoFormatter.string(from: event.startDate),
            "end": event.isAllDay ? dateOnlyFormatter.string(from: event.endDate) : isoFormatter.string(from: event.endDate),
            "all_day": event.isAllDay,
            "location": event.location ?? "",
            "calendar": event.calendar.title,
        ]
        results.append(dict)
    }

    let output: [String: Any] = ["events": results, "count": results.count]
    let data = try! JSONSerialization.data(withJSONObject: output, options: [.sortedKeys])
    print(String(data: data, encoding: .utf8)!)
    exit(0)
}

print("{\"error\": \"Unknown command: \(command)\"}")
exit(1)
