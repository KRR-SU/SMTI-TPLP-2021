//
// Toolkit constraint encoding
//

import java.io.*;
import java.util.*;
import java.util.regex.*;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.Solution;
import org.chocosolver.solver.Solver;
import org.chocosolver.solver.exception.ContradictionException;
import org.chocosolver.solver.variables.BoolVar;
import org.chocosolver.solver.variables.IntVar;
import org.chocosolver.solver.variables.SetVar;
import org.chocosolver.util.iterators.DisposableValueIterator;
import org.chocosolver.util.tools.ArrayUtils;
import org.chocosolver.solver.search.strategy.Search;
import org.chocosolver.solver.constraints.extension.Tuples;

public class SMTI_maxcard {

	int n;
	List<List<List<Integer>>> mprefList = new ArrayList<>();
	List<List<List<Integer>>> wprefList = new ArrayList<>();
	List<List<Integer>> flat_mprefList = new ArrayList<>();
	List<List<Integer>> flat_wprefList = new ArrayList<>();
	Model model;
	Solver solver;
	IntVar[] men; // domain of length of preference list
	IntVar[] women; // domain of length of preference list
	IntVar objective;
	long totalTime, modelTime, solveTime, readTime, modelSize;
	boolean search;
	int solutions, matchingSize;

	SMTI_maxcard(String fname) throws IOException {
		search = true;
		totalTime = System.currentTimeMillis();
		readTime = System.currentTimeMillis();
		read(fname);
		readTime = System.currentTimeMillis() - readTime;
	}

	void read(String fname) throws IOException {
		BufferedReader fin = new BufferedReader(new FileReader(fname));
		fin.readLine();
		n = Integer.parseInt(fin.readLine());
        List<Integer> single = Arrays.asList(n+1);
		fin.readLine();

		for (int i = 0; i < n; i++) {
			String[] matches = Pattern.compile("(\\([\\d+ ]+\\))")
                          .matcher(fin.readLine())
                          .results()
                          .map(MatchResult::group)
                          .toArray(String[]::new);
			int k = 0;
            List<List<Integer>> mplist = new ArrayList<>();
            mprefList.add(mplist); 
			for (int z = 0; z < matches.length; z++) {
				int cl = matches[z].length();
				String[] items = matches[z].replaceAll("\\(","").replaceAll("\\)","").split(" ");
				List<Integer> tieGroup = new ArrayList<>();
				for(int m = 0; m < items.length; m++)
				{
				    tieGroup.add(Integer.parseInt(items[m]));
				}
				mplist.add(tieGroup);
			}
            mplist.add(single);
		}

		for (int i = 0; i < n; i++) {
			String[] matches = Pattern.compile("(\\([\\d+ ]+\\))")
                          .matcher(fin.readLine())
                          .results()
                          .map(MatchResult::group)
                          .toArray(String[]::new);
			int k = 0;
            List<List<Integer>> wplist = new ArrayList<>();
            wprefList.add(wplist); 
			for (int z = 0; z < matches.length; z++) {
				int cl = matches[z].length();
				String[] items = matches[z].replaceAll("\\(","").replaceAll("\\)","").split(" ");
				List<Integer> tieGroup = new ArrayList<>();
				for(int m = 0; m < items.length; m++)
				{
				    tieGroup.add(Integer.parseInt(items[m]));
				}
				wplist.add(tieGroup);
			}
            wplist.add(single);
		}
		fin.close();
		for (int i = 0; i < n; i++) {
            flat_mprefList.add(macceptableList(i));
		}
		for (int i = 0; i < n; i++) {
            flat_wprefList.add(wacceptableList(i));
		}
	}
    
	List<Integer> macceptableList(int n){
		List<Integer> acc = new ArrayList<>();
		for (int i=0; i < mprefList.get(n).size(); i++){
			for (int j=0; j <  mprefList.get(n).get(i).size(); j++){
                acc.add(mprefList.get(n).get(i).get(j));
		   }
		}
		return acc;
	}

	List<Integer> wacceptableList(int n){
		List<Integer> acc = new ArrayList<>();
		for (int i=0; i < wprefList.get(n).size(); i++){
			for (int j=0; j <  wprefList.get(n).get(i).size(); j++){
                acc.add(wprefList.get(n).get(i).get(j));
		   }
		}
		return acc;
	}

	int mposInList(int n, int el){
		int pos = 0;
		for (int i=0; i < mprefList.get(n).size(); i++){
            if(mprefList.get(n).get(i).contains(el)){
				return pos;
			}
			else
				pos += 1;
		   }
		return -1;
	}

	int wposInList(int n, int el){
		int pos = 0;
		for (int i=0; i < wprefList.get(n).size(); i++){
            if(wprefList.get(n).get(i).contains(el)){
				return pos;
			}
			else
				pos += 1;
		   }
		return -1;
	}

	int mposInArray(int n, int el){
		int pos = 0;
		for (int i=0; i < flat_mprefList.get(n).size(); i++){
            if(flat_mprefList.get(n).get(i) == el){
				return pos;
			}
			else
				pos += 1;
		   }
		return -1;
	}

	int wposInArray(int n, int el){
		int pos = 0;
		for (int i=0; i < flat_wprefList.get(n).size(); i++){
            if(flat_wprefList.get(n).get(i) == el){
				return pos;
			}
			else
				pos += 1;
		   }
		return -1;
	}

	int[] findNext(int i, int j){
        int z = mposInList(i, j+1) + 1;
		if(z == mprefList.get(i).size()){
           z = -1;
		}
		int k = wposInList(j, i+1) + 1;
		if(k == wprefList.get(j).size()){
           k = -1;
		}
		if(z != -1 && k != -1){
			z = mposInArray(i, mprefList.get(i).get(z).get(0));
			k = wposInArray(j, wprefList.get(j).get(k).get(0));
		}
		int[] res = new int[2];
		res[0] = z;
		res[1] = k;
		return res;
	}

	void build() {
		modelTime = System.currentTimeMillis();
		model = new Model();		
		men = new IntVar[n];
		women = new IntVar[n];
		
		//define variables 
		for (int i=0;i<n;i++){
			int[] domset = macceptableList(i).stream().mapToInt(Integer::intValue).toArray();
			men[i] = model.intVar("m_" + Integer.toString(i), domset);
		}

		//define variables 
		for (int i=0;i<n;i++){
			int[] domset = wacceptableList(i).stream().mapToInt(Integer::intValue).toArray();;
			women[i] = model.intVar("w_" + Integer.toString(i), domset);
		}
        
		for (int i=0; i < n; i++){
			for (int j=0; j < n; j++){
			    int mwi = mposInList(i, j+1);
                int wmi = wposInList(j, i+1);
                if(mwi != -1 && wmi != -1){
				    List<Integer> flat_mpref = macceptableList(i);
                    List<Integer> flat_wpref = wacceptableList(j);
					int updatedi = mposInArray(i, j+1);
					int updatedj = wposInArray(j, i+1);
                    for (int k = 0; k < flat_mpref.size(); k++){
                        if(k != updatedi)
						   {
                            model.ifThen(model.arithm(men[i], "=", flat_mpref.get(k)), model.arithm(women[j], "!=", i+1));
					      }
				    }
                    for (int l = 0; l < flat_wpref.size(); l++){
                        if(l != updatedj)
						   {
                            model.ifThen(model.arithm(women[j], "=", flat_wpref.get(l)), model.arithm(men[i], "!=", j+1));
					      }
				    }		
					int[] next = findNext(i, j);
					if(next[0] != -1 && next[1] != -1){
						for (int k = next[0]; k < flat_mpref.size(); k++){
							for (int l = next[1]; l < flat_wpref.size(); l++){
								model.ifThen(model.arithm(women[j], "=", flat_wpref.get(l)), model.arithm(men[i], "!=", flat_mpref.get(k)));
			                }
				        }
		            }
		   }
		 } 
		}
        objective = model.intVar(0, n);
        BoolVar[] matched = new BoolVar[n];
        for(int i=0; i < n; i++){
            BoolVar bv = model.boolVar(Integer.toString(i));
            model.ifOnlyIf(model.arithm(bv, "=", 0), model.arithm(men[i], "=", n+1));
            matched[i] = bv;
        }
        model.sum(matched, "=", objective).post();
        model.setObjective(Model.MAXIMIZE, objective);
		solver = model.getSolver();
    	modelTime = System.currentTimeMillis() - modelTime;
    	modelSize = (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024; // kilobytes
        
	 }

	void solve() throws ContradictionException {
		solutions = matchingSize = 0;
		solveTime = System.currentTimeMillis();
		//solver.setVarIntSelector(new StaticVarOrder(solver,solver.getVar(agent)));
        int[] mvals = new int[n];
        int o = 0;
		//if (command.equals("count")) { // count all solutions
	while (solver.solve()) {
	     for (int i = 0; i < n; i++) {
                   mvals[i] = men[i].getValue();
             }
             o = objective.getValue();
             solutions += 1;
         }
         System.out.println("Optimal val: " + Integer.toString(o));
         System.out.println("m");
         for (int i = 0; i < n; i++) {
           System.out.println("(" + (i + 1) + "," + (mvals[i]) + ") ");
         }
		solveTime = System.currentTimeMillis() - solveTime;
		totalTime = System.currentTimeMillis() - totalTime;
	}

	// int getMatchingSize() {
	// 	matchingSize = 0;
	// 	for (int i = 0; i < n; i++)
	// 		if (men[i].getValue() < mlength[i])
	// 			matchingSize++;
	// 	return matchingSize;
	// }

	// void displayPhase1Table() {
	// 	for (int i = 0; i < n; i++) {
	// 		IntVar v = agent[i];
	// 		System.out.print(i + 1 + ": ");
	// 		DisposableValueIterator iterator = v.getValueIterator(false);
	// 		int j;
	// 		while (iterator.hasNext()) {
	// 			j = iterator.next();
	// 			System.out.print(pref[i][j] + 1 + " ");
	// 		}
	// 		System.out.println();
	// 	}
	// }
	// void display() {
	// 	System.out.println(n);
	// 	for (int i = 0; i < n; i++) {
	// 		for (int j = 0; j < n; j++)
	// 			if (pref[i][j] != i)
	// 				System.out.print((pref[i][j] + 1) + " ");
	// 		System.out.println();
	// 	}
	// }
	void stats(){
		solver.printStatistics();
		// System.out.print("solutions: "+ solutions +" ");
		// if (search) System.out.print("nodes: "+ solver.getNodeCount() +"  ");
		// System.out.print("modelTime: "+ modelTime +"  ");
		// if (search) System.out.print("solveTime: "+ solveTime +"  ");
		// System.out.print("totalTime: "+ totalTime +"  ");
		// System.out.print("modelSize: "+ modelSize +"  ");
		// System.out.print("readTime: "+ readTime +" ");
		// System.out.println();
	}
	public static void main(String[] args) throws IOException, ContradictionException {
		SMTI_maxcard sm = new SMTI_maxcard(args[0]);
		sm.build();
		sm.solve();
		sm.stats();
	}
}
