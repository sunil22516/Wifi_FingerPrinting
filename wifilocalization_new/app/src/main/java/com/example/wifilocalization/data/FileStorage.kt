package com.example.wifilocalization.data

import android.content.Context
import android.util.Log
import java.io.File

object FileStorage {

    private const val FILE_NAME = "fingerprints.csv"

//    fun saveFingerprint(context: Context, fp: Fingerprint) {
//
//        val file = File(context.filesDir, FILE_NAME)
//
//        val line = buildString {
//            append(fp.location)
//
//            fp.wifiMap.forEach { (bssid, rssi) ->
//                append(",$bssid:$rssi")
//            }
//
//            append("\n")
//        }
//
//        file.appendText(line)
//    }
//fun saveFingerprint(context: Context, fp: Fingerprint) {
//
//    val file = File(context.filesDir, FILE_NAME)
//
//    val line = buildString {
//        append(fp.location)
//
//        fp.wifiMap.forEach { (bssid, rssi) ->
//            append(",$bssid:$rssi")
//        }
//
//        append("\n")
//    }
//
//    file.appendText(line)
//
//    println("Fingerprint saved at: ${file.absolutePath}")
//}

    fun saveFingerprint(context: Context, fp: Fingerprint) {

        val file = File(context.filesDir, FILE_NAME)

        val line = buildString {

            append("${fp.timestamp},${fp.location}")

            fp.wifiMap.forEach { (bssid, rssi) ->
                append(",$bssid:$rssi")
            }

            append("\n")
        }

        file.appendText(line)
        Log.d("FILE_SAVE", "Saved fingerprint: ${fp.location}")
        Log.d("FILE_SAVE", "File path: ${file.absolutePath}")
        Log.d("FILE_SAVE", "File exists: ${file.exists()}")
    }

    fun loadFingerprints(context: Context): List<Fingerprint> {

        val file = File(context.filesDir, FILE_NAME)

        if (!file.exists()) return emptyList()

//        return file.readLines().map { line ->
//
//            val parts = line.split(",")
//
////            val location = parts[0]
//            val timestamp = parts[0]
//            val location = parts[1]
//
//            val map = parts.drop(2).associate {
//
//                val pair = it.split(":")
//                pair[0] to pair[1].toInt()
//            }
//
//            Fingerprint(location, map, timestamp)
//        }

        return file.readLines().mapNotNull { line ->

            try {

//                val parts = line.split(",")
                val parts = line.split(",", "\t")
                if (parts.size < 3) return@mapNotNull null

                val timestamp = parts[0]
                val location = parts[1]

                val map = parts.drop(2).mapNotNull {

//                    val pair = it.split(":")
//                    val rssi = pair.getOrNull(1)?.toIntOrNull()
//
//                    if (rssi != null) pair[0] to rssi else null
                    val lastColon = it.lastIndexOf(":")

                    if (lastColon != -1) {
                        val bssid = it.substring(0, lastColon)
                        val rssi = it.substring(lastColon + 1).toIntOrNull()
                        if (rssi != null) bssid to rssi else null
                    } else null

                }.toMap()

                Fingerprint(location, map, timestamp)

            } catch (e: Exception) {
                null
            }
        }
    }

//    fun deleteByLocation(context: Context, locationName: String) {
//
//        val file = File(context.filesDir, FILE_NAME)
//
//        if (!file.exists()) return
//
//        val updatedLines = file.readLines().filterNot { line ->
//            val parts = line.split(",", "\t")
//            val location = parts.getOrNull(1)
//            location == locationName
//        }
fun deleteByLocation(context: Context, locationName: String) {

    val file = File(context.filesDir, FILE_NAME)
    if (!file.exists()) return

//    val updatedLines = file.readLines().filterNot { line ->
//
//        val parts = line.split(",", limit = 3)
//        val location = parts.getOrNull(1)
//
//        location == locationName
//    }
    val updatedLines = file.readLines().filterNot { line ->

        val parts = line.split(",", limit = 3)
        val location = parts.getOrNull(1)?.trim()

        location.equals(locationName.trim(), ignoreCase = true)
    }

    file.writeText(updatedLines.joinToString("\n") + "\n")

    Log.d("FILE_DELETE", "Deleted entries for: $locationName")
}
}
