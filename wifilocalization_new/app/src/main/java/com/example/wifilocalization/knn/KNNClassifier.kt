//TRY1
//package com.example.wifilocalization.knn
//
//import com.example.wifilocalization.data.Fingerprint
//import kotlin.math.sqrt
//
//class KNNClassifier {
//
//    fun predict(current: List<Int>, dataset: List<Fingerprint>, k: Int = 3): String {
//
//        if (dataset.isEmpty()) return "No Data"
//
//        val distances = dataset.map {
//            val dist = euclidean(current, it.rssiValues)
//            Pair(it.location, dist)
//        }
//
//        val nearest = distances.sortedBy { it.second }.take(k)
//
//        return nearest.groupBy { it.first }
//            .maxByOrNull { it.value.size }?.key ?: "Unknown"
//    }
//
//    private fun euclidean(a: List<Int>, b: List<Int>): Double {
//
//        val size = minOf(a.size, b.size)
//        var sum = 0.0
//
//        for (i in 0 until size) {
//            val diff = a[i] - b[i]
//            sum += diff * diff
//        }
//
//        return sqrt(sum)
//    }
//}


// TRY2
//package com.example.wifilocalization.knn
//
//import com.example.wifilocalization.data.Fingerprint
//import kotlin.math.sqrt
//
//class KNNClassifier {
//
//    fun predict(
//        current: Map<String, Int>,
//        dataset: List<Fingerprint>,
//        k: Int = 3
//    ): String {
//
//        if (dataset.isEmpty()) return "No Data"
//
//        val distances = dataset.map {
//
//            val dist = calculateDistance(current, it.wifiMap)
//            Pair(it.location, dist)
//        }
//
//        val nearest = distances.sortedBy { it.second }.take(k)
//
//        return nearest.groupBy { it.first }
//            .maxByOrNull { it.value.size }?.key ?: "Unknown"
//    }
//
//    private fun calculateDistance(
//        current: Map<String, Int>,
//        stored: Map<String, Int>
//    ): Double {
//
//        val allKeys = current.keys + stored.keys
//
//        var sum = 0.0
//
//        for (key in allKeys) {
//
//            val rssi1 = current[key] ?: -100 // missing AP = very weak
//            val rssi2 = stored[key] ?: -100
//
//            val diff = rssi1 - rssi2
//            sum += diff * diff
//        }
//
//        return sqrt(sum)
//    }
//}

//TRY3
package com.example.wifilocalization.knn

import com.example.wifilocalization.data.Fingerprint
import kotlin.math.sqrt

class KNNClassifier {

    fun predict(
        current: Map<String, Int>,
        dataset: List<Fingerprint>,
        k: Int = 3
    ): String {

        if (dataset.isEmpty()) return "No Data"


        val balancedDataset = dataset
            .groupBy { it.location }
            .flatMap { (_, list) -> list.take(17) }  // limit per location
        val distances = balancedDataset.map{

            val dist = calculateDistance(current, it.wifiMap)
            Pair(it.location, dist)
        }
//        val distances = dataset.map {
//
//            val dist = calculateDistance(current, it.wifiMap)
//            Pair(it.location, dist)
//        }

        val nearest = distances.sortedBy { it.second }.take(k)

        return nearest.groupBy { it.first }
            .maxByOrNull { it.value.size }?.key ?: "Unknown"
    }

    private fun calculateDistance(
        current: Map<String, Int>,
        stored: Map<String, Int>
    ): Double {

        val allKeys = current.keys + stored.keys

        var sum = 0.0

        for (key in allKeys) {

            val rssi1 = current[key] ?: -100
            val rssi2 = stored[key] ?: -100

            val diff = rssi1 - rssi2
            sum += diff * diff
        }

        return sqrt(sum)
    }
}